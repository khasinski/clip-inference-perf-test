defmodule FastClipEx.MixProject do
  use Mix.Project

  def project do
    [
      app: :fast_clip_ex,
      version: "0.1.0",
      elixir: "~> 1.19",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  # Run "mix help compile.app" to learn about applications.
  def application do
    [
      extra_applications: [:logger],
      mod: {FastClipEx.Application, []}
    ]
  end

  # Run "mix help deps" to learn about dependencies.
  defp deps do
    [
      {:plug, "~> 1.15"},
      {:bandit, "~> 1.0"},
      {:jason, "~> 1.4"},
      {:ortex, "~> 0.1"},
      {:tokenizers, "~> 0.5"}
    ]
  end
end
