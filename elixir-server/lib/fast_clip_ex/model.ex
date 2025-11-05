defmodule FastClipEx.Model do
  @moduledoc """
  Manages ONNX model and tokenizer for text encoding.
  """
  use GenServer
  require Logger

  @model_path "../model/model_quantized.onnx"
  @tokenizer_path "../model"

  # Client API

  def start_link(_opts) do
    GenServer.start_link(__MODULE__, %{}, name: __MODULE__)
  end

  @doc """
  Encode texts to embeddings.
  Returns {:ok, embeddings} or {:error, reason}.
  """
  def encode(texts, normalize \\ true) when is_list(texts) do
    GenServer.call(__MODULE__, {:encode, texts, normalize}, 30_000)
  end

  # Server Callbacks

  @impl true
  def init(_) do
    Logger.info("Loading ONNX model and tokenizer...")

    # Get project root and construct absolute paths
    project_root = File.cwd!()
    model_full_path = Path.join([project_root, @model_path])
    tokenizer_full_path = Path.join([project_root, @tokenizer_path])

    Logger.info("Model path: #{model_full_path}")
    Logger.info("Tokenizer path: #{tokenizer_full_path}")

    # Load ONNX model
    model = Ortex.load(model_full_path)

    # Load tokenizer
    {:ok, tokenizer} = Tokenizers.Tokenizer.from_file(Path.join(tokenizer_full_path, "tokenizer.json"))

    Logger.info("Model and tokenizer loaded successfully!")

    {:ok, %{model: model, tokenizer: tokenizer}}
  end

  @impl true
  def handle_call({:encode, texts, normalize}, _from, state) do
    result = do_encode(texts, normalize, state)
    {:reply, result, state}
  end

  # Private Functions

  defp do_encode(texts, normalize, %{model: model, tokenizer: tokenizer}) do
    try do
      # Tokenize texts
      {:ok, encoding} = Tokenizers.Tokenizer.encode_batch(tokenizer, texts,
        add_special_tokens: true
      )

      # Extract token IDs and attention masks
      input_ids = Enum.map(encoding, &Tokenizers.Encoding.get_ids/1)
      attention_mask = Enum.map(encoding, &Tokenizers.Encoding.get_attention_mask/1)

      # Find max length for padding
      max_len = Enum.map(input_ids, &length/1) |> Enum.max()

      # Pad sequences
      input_ids_padded = Enum.map(input_ids, fn ids ->
        ids ++ List.duplicate(0, max_len - length(ids))
      end)

      attention_mask_padded = Enum.map(attention_mask, fn mask ->
        mask ++ List.duplicate(0, max_len - length(mask))
      end)

      # Convert to tensors
      batch_size = length(texts)
      input_ids_tensor = Nx.tensor(input_ids_padded, type: :s64) |> Nx.reshape({batch_size, max_len})
      attention_mask_tensor = Nx.tensor(attention_mask_padded, type: :s64) |> Nx.reshape({batch_size, max_len})

      # Run inference
      {embeddings} = Ortex.run(model, {input_ids_tensor, attention_mask_tensor})

      # Convert to BinaryBackend for normalization operations
      embeddings = Nx.backend_transfer(embeddings, Nx.BinaryBackend)

      # Normalize if requested
      embeddings = if normalize do
        normalize_embeddings(embeddings)
      else
        embeddings
      end

      # Convert to list for JSON serialization
      embeddings_list = Nx.to_list(embeddings)
      shape = Tuple.to_list(Nx.shape(embeddings))

      {:ok, %{embeddings: embeddings_list, shape: shape}}
    rescue
      e -> {:error, Exception.message(e)}
    end
  end

  defp normalize_embeddings(tensor) do
    # Compute L2 norm along the last dimension
    norms = Nx.sqrt(Nx.sum(Nx.pow(tensor, 2), axes: [-1], keep_axes: true))
    # Avoid division by zero
    norms = Nx.select(Nx.equal(norms, 0), Nx.tensor(1.0), norms)
    # Normalize
    Nx.divide(tensor, norms)
  end
end
