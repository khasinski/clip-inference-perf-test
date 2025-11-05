<?php
require_once __DIR__ . '/vendor/autoload.php';

use Codewithkyrian\Transformers\OnnxRuntime\InferenceSession;

// Configuration
const MODEL_PATH = __DIR__ . '/../model/model_quantized.onnx';
const TOKENIZER_PATH = __DIR__ . '/../model/tokenizer.json';
const PORT = 8004;
const HOST = '0.0.0.0';

class SimpleTokenizer {
    private array $vocab;
    private array $merges;

    public function __construct(string $tokenizerPath) {
        $config = json_decode(file_get_contents($tokenizerPath), true);

        // Load vocabulary
        $this->vocab = $config['model']['vocab'] ?? [];

        // Simple whitespace and punctuation tokenization
    }

    public function encode(string $text): array {
        // Lowercase and basic cleaning
        $text = strtolower(trim($text));

        // Simple word tokenization
        $words = preg_split('/\s+/', $text);

        // Map to token IDs
        $token_ids = [49406]; // Start token for CLIP

        foreach ($words as $word) {
            // Try to find exact match
            if (isset($this->vocab[$word])) {
                $token_ids[] = $this->vocab[$word];
            } else {
                // Try character-level fallback
                for ($i = 0; $i < strlen($word); $i++) {
                    $char = $word[$i];
                    if (isset($this->vocab[$char])) {
                        $token_ids[] = $this->vocab[$char];
                    }
                }
            }
        }

        $token_ids[] = 49407; // End token for CLIP

        // Attention mask (all 1s for actual tokens)
        $attention_mask = array_fill(0, count($token_ids), 1);

        return [
            'ids' => $token_ids,
            'attention_mask' => $attention_mask
        ];
    }
}

class FastClipServer {
    private InferenceSession $session;
    private SimpleTokenizer $tokenizer;

    public function __construct() {
        echo "🐘 Loading ONNX model and tokenizer...\n";
        echo "   Using: PHP + ONNXRuntime (Simple Tokenizer)\n";
        echo "   Model path: " . MODEL_PATH . "\n";

        // Load ONNX inference session
        $this->session = new InferenceSession(MODEL_PATH);

        // Load simple tokenizer
        $this->tokenizer = new SimpleTokenizer(TOKENIZER_PATH);

        echo "   Model and tokenizer loaded successfully!\n";
        echo "🚀 Server listening on http://" . HOST . ":" . PORT . "\n";
    }

    public function handleRequest(): void {
        // Set JSON content type
        header('Content-Type: application/json');

        // Parse request
        $method = $_SERVER['REQUEST_METHOD'];
        $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

        try {
            if ($path === '/encode' && $method === 'POST') {
                $this->handleEncode();
            } elseif ($path === '/health' && $method === 'GET') {
                $this->handleHealth();
            } else {
                http_response_code(404);
                echo json_encode(['error' => 'Not found']);
            }
        } catch (Throwable $e) {
            http_response_code(500);
            echo json_encode([
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
        }
    }

    private function handleEncode(): void {
        // Parse JSON body
        $body = file_get_contents('php://input');
        $data = json_decode($body, true);

        $texts = $data['texts'];
        $normalize = $data['normalize'] ?? true;

        if (!is_array($texts)) {
            http_response_code(400);
            echo json_encode(['error' => 'Missing or invalid texts parameter']);
            return;
        }

        // Tokenize texts
        $encodings = array_map(fn($text) => $this->tokenizer->encode($text), $texts);
        $inputIds = array_map(fn($enc) => $enc['ids'], $encodings);
        $attentionMasks = array_map(fn($enc) => $enc['attention_mask'], $encodings);

        // Pad sequences
        $maxLen = max(array_map('count', $inputIds));
        $inputIdsPadded = array_map(
            fn($ids) => array_pad($ids, $maxLen, 0),
            $inputIds
        );
        $attentionMasksPadded = array_map(
            fn($mask) => array_pad($mask, $maxLen, 0),
            $attentionMasks
        );

        // Run inference
        $outputs = $this->session->run(null, [
            'input_ids' => $inputIdsPadded,
            'attention_mask' => $attentionMasksPadded
        ]);

        // Get embeddings (first output)
        $embeddings = $outputs[0];

        // Normalize if requested
        if ($normalize) {
            $embeddings = $this->normalizeEmbeddings($embeddings);
        }

        // Return result
        echo json_encode([
            'embeddings' => $embeddings,
            'shape' => [count($embeddings), count($embeddings[0])]
        ]);
    }

    private function handleHealth(): void {
        echo json_encode([
            'status' => 'ready',
            'provider' => 'PHP + ONNXRuntime + Simple Tokenizer'
        ]);
    }

    private function normalizeEmbeddings(array $embeddings): array {
        $normalized = [];

        foreach ($embeddings as $embedding) {
            // Calculate L2 norm
            $norm = sqrt(array_sum(array_map(fn($x) => $x * $x, $embedding)));

            // Avoid division by zero
            if ($norm == 0) {
                $norm = 1.0;
            }

            // Normalize
            $normalized[] = array_map(fn($x) => $x / $norm, $embedding);
        }

        return $normalized;
    }
}

// Start server
$server = new FastClipServer();
$server->handleRequest();
