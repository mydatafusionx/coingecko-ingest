package com.datafusion.ingest;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.TimeUnit;

/**
 * Utility class for ingesting data from CoinGecko API.
 */
public final class CoinGeckoIngest {
    /** HTTP client for making API requests. */
    private static final OkHttpClient CLIENT = new OkHttpClient();

    /** Base URL for CoinGecko API. */
    private static final String BASE_URL = "https://api.coingecko.com/api/v3";

    /** Path to store raw data files. */
    private static final String RAW_PATH = "/data/raw/";

    /** Date formatter for timestamp. */
    private static final DateTimeFormatter TIMESTAMP_FORMATTER =
        DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss");

    /** Maximum number of retries for API calls. */
    private static final int MAX_RETRIES = 3;

    /** Initial delay between retries in milliseconds. */
    private static final long INITIAL_RETRY_DELAY_MS = 2000;

    /**
     * Private constructor to prevent instantiation.
     */
    private CoinGeckoIngest() {
        throw new UnsupportedOperationException("Utility class");
    }

    /**
     * Main method to fetch and save data from CoinGecko API.
     *
     * @param args command line arguments (not used)
     */
    public static void main(final String[] args) {
        // Configure HTTP client with timeouts
        OkHttpClient client = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();

        // Execute API calls with rate limiting
        executeWithRetry(client, "/coins/list", "coins_list");
        // Add delay between API calls to respect rate limits
        sleep(2000);
        executeWithRetry(client, "/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", "simple_price");
        sleep(2000);
        executeWithRetry(client, "/coins/bitcoin/market_chart?vs_currency=usd&days=1", "market_chart_bitcoin");
        sleep(2000);
        executeWithRetry(client, "/coins/ethereum/market_chart?vs_currency=usd&days=1", "market_chart_ethereum");
    }

    /**
     * Executes an API call with retry logic.
     *
     * @param client the HTTP client to use
     * @param endpoint the API endpoint to call
     * @param prefix the prefix for the output file
     */
    private static void executeWithRetry(OkHttpClient client, String endpoint, String prefix) {
        int attempt = 0;
        long delayMs = INITIAL_RETRY_DELAY_MS;
        
        while (attempt < MAX_RETRIES) {
            attempt++;
            try {
                System.out.println(String.format("Attempt %d/%d for %s", attempt, MAX_RETRIES, prefix));
                fetchAndSave(client, endpoint, prefix);
                return; // Success, exit the retry loop
            } catch (IOException e) {
                if (attempt >= MAX_RETRIES) {
                    System.err.println(String.format("Failed to fetch %s after %d attempts: %s", 
                        prefix, MAX_RETRIES, e.getMessage()));
                    return;
                }
                
                // If rate limited, wait longer
                if (e.getMessage() != null && e.getMessage().contains("429")) {
                    System.out.println(String.format("Rate limited. Waiting %d ms before retry...", delayMs));
                    sleep(delayMs);
                    // Exponential backoff with jitter
                    delayMs = (long) (delayMs * 2.5 + (Math.random() * 1000));
                } else {
                    // For other errors, use a smaller delay
                    sleep(1000);
                }
            }
        }
    }

    /**
     * Fetches data from the specified endpoint and saves it to a file.
     *
     * @param client the HTTP client to use
     * @param endpoint the API endpoint to fetch data from
     * @param prefix the prefix to use for the output file
     * @throws IOException if an I/O error occurs
     */
    private static void fetchAndSave(
            OkHttpClient client,
            String endpoint,
            String prefix
    ) throws IOException {
        String url = BASE_URL + endpoint;
        Request request = new Request.Builder()
            .url(url)
            .addHeader("User-Agent", "Mozilla/5.0")
            .build();

        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException(String.format("Unexpected code %d for URL: %s", 
                    response.code(), url));
            }

            String responseBody = response.body() != null ? response.body().string() : "";
            if (responseBody.trim().isEmpty()) {
                throw new IOException("Empty response received from " + url);
            }

            String timestamp = LocalDateTime.now().format(TIMESTAMP_FORMATTER);
            File dir = new File(RAW_PATH);
            if (!dir.exists() && !dir.mkdirs()) {
                throw new IOException("Failed to create directory: " + dir.getAbsolutePath());
            }

            String filename = String.format(
                "%s%s_%s.json",
                RAW_PATH,
                prefix,
                timestamp
            );

            try (FileWriter writer = new FileWriter(filename)) {
                writer.write(responseBody);
                System.out.println("Saved: " + prefix + " at " + timestamp);
            }
        }
    }

    /**
     * Sleeps for the specified number of milliseconds.
     *
     * @param millis the number of milliseconds to sleep
     */
    private static void sleep(long millis) {
        try {
            Thread.sleep(millis);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            System.err.println("Sleep interrupted: " + e.getMessage());
        }
    }
}
