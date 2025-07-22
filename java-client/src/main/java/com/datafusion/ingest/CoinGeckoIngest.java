package com.datafusion.ingest;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

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
     * @throws IOException if an I/O error occurs
     */
    public static void main(final String[] args) throws IOException {
        fetchAndSave(
            "/coins/list",
            "coins_list"
        );
        fetchAndSave(
            "/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
            "simple_price"
        );
        fetchAndSave(
            "/coins/bitcoin/market_chart?vs_currency=usd&days=1",
            "market_chart_bitcoin"
        );
        fetchAndSave(
            "/coins/ethereum/market_chart?vs_currency=usd&days=1",
            "market_chart_ethereum"
        );
    }

    /**
     * Fetches data from the specified endpoint and saves it to a file.
     *
     * @param endpoint the API endpoint to fetch data from
     * @param prefix the prefix to use for the output file
     * @throws IOException if an I/O error occurs
     */
    private static void fetchAndSave(
            final String endpoint,
            final String prefix
    ) throws IOException {
        String url = BASE_URL + endpoint;
        Request request = new Request.Builder()
            .url(url)
            .build();

        try (Response response = CLIENT.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected code " + response);
            }

            String timestamp = LocalDateTime.now().format(TIMESTAMP_FORMATTER);
            File dir = new File(RAW_PATH);
            if (!dir.exists()) {
                dir.mkdirs();
            }

            String filename = String.format(
                "%s%s_%s.json",
                RAW_PATH,
                prefix,
                timestamp
            );

            try (FileWriter writer = new FileWriter(filename)) {
                writer.write(response.body().string());
                System.out.println("Saved: " + prefix + " at " + timestamp);
            }
        }
    }
}
