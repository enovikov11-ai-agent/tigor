package rs.tgr.codeworld;

import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.entity.Player;
import org.bukkit.*;

import com.sun.net.httpserver.*;
import com.google.gson.Gson;

import java.io.*;
import java.net.*;
import java.util.*;

@SuppressWarnings("restriction")
public class CodeWorld extends JavaPlugin {
    private static final int CHUNK_SIZE = 16;
    private static final int MIN_Y = -64;
    private static final int MAX_Y = 320;

    private static final String WORLD_NAME = "world";
    private static final String BIND_ADDR = "0.0.0.0";
    private static final int PORT = 1337;

    private static final int BYTE_SIZE = 256;

    public static class MetaChunk {
        public int x;
        public int z;
        public int lo;
        public int hi;
    }

    public static class ChunksMeta {
        public String[] materials;
        public MetaChunk[] chunks;
    }

    public static class BlocksMeta {
        public String[] materials;
        public int x;
        public int y;
        public int z;
    }

    public static class CodeWorldException extends Exception {
        public CodeWorldException(String message) {
            super(message);
        }
    }

    @Override
    public void onEnable() {
        try {
            HttpServer server = HttpServer.create(new InetSocketAddress(BIND_ADDR, PORT), 0);
            server.createContext("/", new CodeWorldHandler(this));
            server.setExecutor(null);
            server.start();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public String getStats() {
        World world = Bukkit.getWorld(WORLD_NAME);
        Map<String, Object> stats = new HashMap<>();

        List<Map<String, Integer>> chunkList = new ArrayList<>();
        for (Chunk chunk : Bukkit.getWorld(WORLD_NAME).getLoadedChunks()) {
            Map<String, Integer> chunkMap = new HashMap<>();

            chunkMap.put("x", chunk.getX());
            chunkMap.put("z", chunk.getZ());
            chunkList.add(chunkMap);
        }
        stats.put("loaded", chunkList);

        List<Map<String, Integer>> playerList = new ArrayList<>();
        for (Player player : Bukkit.getOnlinePlayers()) {
            Map<String, Integer> playerMap = new HashMap<>();

            if (player.getWorld() == world) {
                playerMap.put("x", (int) player.getLocation().getX() / CHUNK_SIZE);
                playerMap.put("z", (int) player.getLocation().getZ() / CHUNK_SIZE);
                playerList.add(playerMap);
            }
        }
        stats.put("players", playerList);

        return new Gson().toJson(stats);
    }

    public void writeBlocks(BlocksMeta meta, InputStream is) throws CodeWorldException {
        World world = Bukkit.getWorld(WORLD_NAME);
        Location location = new Location(world, 0, 0, 0);
        Material[] materials = Arrays.stream(meta.materials)
                .map(Material::matchMaterial).toArray(Material[]::new);

        try {
            while (true) {
                // Read 4 bytes
                int x = is.read(), y = is.read(), z = is.read(), id = is.read();

                if (x == -1) {
                    break;
                }
                if (y == -1 || z == -1 || id == -1) {
                    throw new EOFException();
                }

                location.setX(meta.x + x);
                location.setY(meta.y + y);
                location.setZ(meta.z + z);
                location.getBlock().setType(materials[id - 1]);
            }
        } catch (IOException e) {
            throw new CodeWorldException("Unexpected end of stream");
        } catch (ArrayIndexOutOfBoundsException e) {
            throw new CodeWorldException("Invalid material");
        }
    }

    public void writeChunks(ChunksMeta meta, InputStream is) throws CodeWorldException {
        World world = Bukkit.getWorld(WORLD_NAME);
        Location location = new Location(world, 0, 0, 0);
        Material[] materials = Arrays.stream(meta.materials)
                .map(Material::matchMaterial).toArray(Material[]::new);

        for (MetaChunk chunk : meta.chunks) {
            if (chunk.lo < MIN_Y || chunk.hi > MAX_Y || chunk.lo >= chunk.hi) {
                throw new CodeWorldException("Chunk size mismatch");
            }

            for (int y = chunk.lo; y < chunk.hi; y++) {
                for (int dx = 0; dx < CHUNK_SIZE; dx++) {
                    for (int dz = 0; dz < CHUNK_SIZE; dz++) {
                        try {
                            // Read byte
                            int id = is.read();
                            if (id == 0) {
                                continue;
                            }
                            if (id == -1) {
                                throw new EOFException();
                            }

                            int x = CHUNK_SIZE * chunk.x + dx;
                            int z = CHUNK_SIZE * chunk.z + dz;

                            location.setX(x);
                            location.setY(y);
                            location.setZ(z);
                            location.getBlock().setType(materials[id - 1]);
                        } catch (IOException e) {
                            throw new CodeWorldException("Unexpected end of stream");
                        } catch (ArrayIndexOutOfBoundsException e) {
                            throw new CodeWorldException("Invalid material");
                        }
                    }
                }
            }
        }
    }
}
