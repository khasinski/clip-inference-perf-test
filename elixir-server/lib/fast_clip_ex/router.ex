defmodule FastClipEx.Router do
  use Plug.Router

  plug Plug.Parsers,
    parsers: [:json],
    pass: ["application/json"],
    json_decoder: Jason

  plug :match
  plug :dispatch

  post "/encode" do
    with {:ok, texts} <- get_texts(conn.body_params),
         normalize <- Map.get(conn.body_params, "normalize", true),
         {:ok, result} <- FastClipEx.Model.encode(texts, normalize) do
      conn
      |> put_resp_content_type("application/json")
      |> send_resp(200, Jason.encode!(result))
    else
      {:error, reason} ->
        conn
        |> put_resp_content_type("application/json")
        |> send_resp(500, Jason.encode!(%{error: to_string(reason)}))
    end
  end

  get "/health" do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(200, Jason.encode!(%{
      status: "ready",
      provider: "Elixir + Ortex + Tokenizers"
    }))
  end

  match _ do
    send_resp(conn, 404, "Not found")
  end

  defp get_texts(%{"texts" => texts}) when is_list(texts), do: {:ok, texts}
  defp get_texts(_), do: {:error, "Missing or invalid 'texts' parameter"}
end
