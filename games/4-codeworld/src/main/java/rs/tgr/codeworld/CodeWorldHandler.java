package rs.tgr.codeworld;

import org.bukkit.*;

import com.sun.net.httpserver.*;
import com.google.gson.Gson;

import java.io.*;
import java.net.*;

@SuppressWarnings("restriction")
public class CodeWorldHandler implements HttpHandler {
    private static CodeWorld codeWorld;

    public CodeWorldHandler(CodeWorld codeWorldInstance) {
        codeWorld = codeWorldInstance;
    }

    @Override
    public void handle(HttpExchange exchange) {
        Bukkit.getScheduler().runTask(codeWorld, () -> {
            String response = "OK";
            int code = HttpURLConnection.HTTP_OK;

            try {
                String path = exchange.getRequestURI().getPath();
                String method = exchange.getRequestMethod();
                String metaHeader = exchange.getRequestHeaders().getFirst("X-Meta");

                if ("GET".equals(method) && "/stats".equals(path)) {
                    exchange.getResponseHeaders().set("Content-Type", "application/json");
                    response = codeWorld.getStats();
                } else if ("POST".equals(method) && "/chunks".equals(path)) {
                    CodeWorld.ChunksMeta meta = new Gson().fromJson(metaHeader, CodeWorld.ChunksMeta.class);
                    codeWorld.writeChunks(meta, exchange.getRequestBody());
                } else if ("POST".equals(method) && "/blocks".equals(path)) {
                    CodeWorld.BlocksMeta meta = new Gson().fromJson(metaHeader, CodeWorld.BlocksMeta.class);
                    codeWorld.writeBlocks(meta, exchange.getRequestBody());
                } else {
                    response = "Not Found";
                    code = HttpURLConnection.HTTP_NOT_FOUND;
                }
            } catch (CodeWorld.CodeWorldException e) {
                response = e.toString();
                code = HttpURLConnection.HTTP_BAD_REQUEST;
            } catch (Exception e) {
                e.printStackTrace();
                response = "Internal Server Error";
                code = HttpURLConnection.HTTP_INTERNAL_ERROR;
            }

            try (OutputStream os = exchange.getResponseBody()) {
                exchange.sendResponseHeaders(code, response.getBytes().length);
                os.write(response.getBytes());
            } catch (Exception e) {
            }
        });
    }
}
