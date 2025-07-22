package com.datafusion.ingest;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class CoinGeckoIngest {
    private static final OkHttpClient client = new OkHttpClient();
    private static final String BASE_URL = "https://api.coingecko.com/api/v3";
    private static final String RAW_PATH = "/data/raw/";

    public static void main(String[] args) throws IOException {
        fetchAndSave("/coins/list", "coins_list");
        fetchAndSave("/simple/price?ids=bitcoin,ethereum&vs_currencies=usd", "simple_price");
        fetchAndSave("/coins/bitcoin/market_chart?vs_currency=usd&days=1", "market_chart_bitcoin");
        fetchAndSave("/coins/ethereum/market_chart?vs_currency=usd&days=1", "market_chart_ethereum");
    }

    private static void fetchAndSave(String endpoint, String prefix) throws IOException {
        String url = BASE_URL + endpoint;
        Request request = new Request.Builder().url(url).build();
        try (Response response = client.newCall(request).execute()) {
            if (!response.isSuccessful()) throw new IOException("Unexpected code " + response);
            String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
            File dir = new File(RAW_PATH);
            if (!dir.exists()) dir.mkdirs();
            FileWriter writer = new FileWriter(RAW_PATH + prefix + "_" + timestamp + ".json");
            writer.write(response.body().string());
            writer.close();
            System.out.println("Saved: " + prefix + " at " + timestamp);
        }
    }
}
