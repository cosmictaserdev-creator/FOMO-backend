package com.trendhopper.services

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

object GroqClient {
    private val apiKey: String by lazy { System.getenv("GROQ_API_KEY") ?: error("GROQ_API_KEY not set") }
    private val client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(30)).build()

    suspend fun chat(messages: List<Map<String, String>>, model: String = "llama-3.3-70b-versatile", temperature: Double = 0.7): String =
        withContext(Dispatchers.IO) {
            val payload = buildJsonObject {
                put("model", model)
                put("temperature", temperature)
                putJsonArray("messages") {
                    messages.forEach { msg ->
                        addJsonObject {
                            msg.forEach { (k, v) -> put(k, v) }
                        }
                    }
                }
            }.toString()
            val request = HttpRequest.newBuilder()
                .uri(URI.create("https://api.groq.com/openai/v1/chat/completions"))
                .header("Authorization", "Bearer $apiKey")
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(payload))
                .build()
            val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
            if (resp.statusCode() >= 400) throw RuntimeException("Groq chat: ${resp.statusCode()} ${resp.body()}")
            val body = Json.parseToJsonElement(resp.body()).jsonObject
            body["choices"]?.jsonArray
                ?.firstOrNull()?.jsonObject
                ?.get("message")?.jsonObject
                ?.get("content")?.jsonPrimitive?.content ?: ""
        }
}
