import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

/** Aplicación de ejemplo: servidor HTTP mínimo sin dependencias externas. */
public final class App {
    private static final int PORT = Integer.parseInt(System.getenv().getOrDefault("PORT", "8080"));

    private App() {}

    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--health")) {
            System.exit(healthy() ? 0 : 1);
        }
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);
        server.createContext("/", ex -> reply(ex, "{\"service\":\"java-demo\",\"status\":\"ok\"}"));
        server.createContext("/health", ex -> reply(ex, "{\"status\":\"healthy\"}"));
        server.start();
        System.out.println("escuchando en " + PORT);
    }

    private static void reply(HttpExchange ex, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().add("Content-Type", "application/json");
        ex.sendResponseHeaders(200, bytes.length);
        try (OutputStream os = ex.getResponseBody()) {
            os.write(bytes);
        }
    }

    private static boolean healthy() {
        try {
            HttpRequest req = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + PORT + "/health")).build();
            return HttpClient.newHttpClient().send(req, HttpResponse.BodyHandlers.discarding()).statusCode() == 200;
        } catch (Exception e) {
            return false;
        }
    }
}
