#!/usr/bin/env ruby
# Falcon server configuration for async concurrency
# Uses fiber-based concurrency for better handling of concurrent requests

require 'async'
require 'async/http/endpoint'
require 'protocol/http/middleware'

# Load the Sinatra app
require_relative 'server'

# Falcon runs Rack apps directly
# The FastClipServer Sinatra app is already Rack-compatible

puts "🦅 Starting Falcon server on http://0.0.0.0:8003"
puts "   Using: Async fibers for concurrency"
puts "   Note: ONNX inference is CPU-bound, async helps with HTTP overhead"

# Run with: bundle exec falcon serve --bind http://0.0.0.0:8003 --config falcon.rb
