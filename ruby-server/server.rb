require 'sinatra/base'
require 'json'
require 'onnxruntime'
require 'tokenizers'
require 'numo/narray'

class FastClipServer < Sinatra::Base
  MODEL_PATH = File.expand_path('../model/model_quantized.onnx', __dir__)
  TOKENIZER_PATH = File.expand_path('../model/tokenizer.json', __dir__)

  configure do
    # Load model and tokenizer at startup
    puts "💎 Loading ONNX model and tokenizer..."
    puts "   Using: ONNXRuntime + Tokenizers"
    puts "   Model path: #{MODEL_PATH}"

    set :model, OnnxRuntime::Model.new(MODEL_PATH)
    set :tokenizer, Tokenizers.from_file(TOKENIZER_PATH)

    puts "   Model and tokenizer loaded successfully!"
  end

  before do
    content_type :json
  end

  post '/encode' do
    begin
      # Parse incoming JSON
      request_data = JSON.parse(request.body.read)

      texts = request_data['texts']
      normalize = request_data.fetch('normalize', true)

      raise 'Missing or invalid texts parameter' unless texts.is_a?(Array)

      # Tokenize texts
      encodings = texts.map { |text| settings.tokenizer.encode(text) }
      input_ids = encodings.map(&:ids)
      attention_masks = encodings.map(&:attention_mask)

      # Pad sequences
      max_len = input_ids.map(&:length).max
      input_ids_padded = input_ids.map { |ids| ids + [0] * (max_len - ids.length) }
      attention_masks_padded = attention_masks.map { |mask| mask + [0] * (max_len - mask.length) }

      # Convert to Numo arrays
      batch_size = texts.length
      input_ids_tensor = Numo::Int64.cast(input_ids_padded).reshape(batch_size, max_len)
      attention_mask_tensor = Numo::Int64.cast(attention_masks_padded).reshape(batch_size, max_len)

      # Run inference
      outputs = settings.model.predict({
        'input_ids' => input_ids_tensor,
        'attention_mask' => attention_mask_tensor
      })

      # Debug: check what we got
      raise "Outputs is nil" if outputs.nil?
      raise "Outputs is empty: #{outputs.inspect}" if outputs.respond_to?(:empty?) && outputs.empty?

      # Get the first output (embeddings) - handle both hash and array returns
      if outputs.is_a?(Hash)
        embeddings = outputs.values.first
      elsif outputs.is_a?(Array)
        embeddings = outputs[0]
      else
        embeddings = outputs
      end

      raise "Embeddings is nil after extraction. Outputs class: #{outputs.class}, keys: #{outputs.keys if outputs.respond_to?(:keys)}" if embeddings.nil?

      # Convert to Numo array if needed
      embeddings = Numo::SFloat.cast(embeddings) unless embeddings.is_a?(Numo::NArray)

      # Normalize if requested
      if normalize
        norms = Numo::NMath.sqrt((embeddings ** 2).sum(axis: 1, keepdims: true))
        norms[norms.eq(0)] = 1.0  # Avoid division by zero
        embeddings = embeddings / norms
      end

      # Return result
      {
        embeddings: embeddings.to_a,
        shape: embeddings.shape
      }.to_json

    rescue => e
      status 500
      { error: e.message }.to_json
    end
  end

  get '/health' do
    {
      status: 'ready',
      provider: 'Ruby + Puma + ONNXRuntime'
    }.to_json
  end

  # Removed run! - using Puma/Rack instead
  # run! if app_file == $0
end
