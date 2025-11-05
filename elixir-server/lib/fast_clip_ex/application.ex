defmodule FastClipEx.Application do
  # See https://hexdocs.pm/elixir/Application.html
  # for more information on OTP Applications
  @moduledoc false

  use Application

  @impl true
  def start(_type, _args) do
    IO.puts("🧪 Starting Elixir server on http://0.0.0.0:8002")
    IO.puts("   Using: Ortex (ONNX Runtime) + Tokenizers")

    children = [
      # Start model loader first
      FastClipEx.Model,
      # Then start the web server
      {Bandit, plug: FastClipEx.Router, scheme: :http, port: 8002}
    ]

    # See https://hexdocs.pm/elixir/Supervisor.html
    # for other strategies and supported options
    opts = [strategy: :one_for_one, name: FastClipEx.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
