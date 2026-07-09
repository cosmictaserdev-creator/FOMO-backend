package com.trendhopper.services

import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import java.net.URI
import java.net.URLEncoder
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration

object SupabaseClient {
    private val url: String by lazy { System.getenv("SUPABASE_URL") ?: error("SUPABASE_URL not set") }
    private val key: String by lazy { System.getenv("SUPABASE_KEY") ?: error("SUPABASE_KEY not set") }
    val json = Json { ignoreUnknownKeys = true; encodeDefaults = true }
    private val client = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .build()

    private fun buildUrl(path: String, query: Map<String, String> = emptyMap()): String {
        val qs = query.entries.joinToString("&") { "${it.key}=${URLEncoder.encode(it.value, "UTF-8")}" }
        return "$url/rest/v1/$path${if (qs.isNotEmpty()) "?$qs" else ""}"
    }

    fun get(path: String, query: Map<String, String> = emptyMap()): String {
        val request = HttpRequest.newBuilder()
            .uri(URI.create(buildUrl(path, query)))
            .header("apikey", key)
            .header("Authorization", "Bearer $key")
            .GET()
            .build()
        val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() >= 400) throw RuntimeException("Supabase GET $path: ${resp.statusCode()} ${resp.body()}")
        return resp.body()
    }

    fun post(path: String, body: Map<String, Any?>): String {
        val jsonBody = mapToJson(body)
        val request = HttpRequest.newBuilder()
            .uri(URI.create(buildUrl(path)))
            .header("apikey", key)
            .header("Authorization", "Bearer $key")
            .header("Content-Type", "application/json")
            .header("Prefer", "return=representation")
            .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
            .build()
        val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() >= 400) throw RuntimeException("Supabase POST $path: ${resp.statusCode()} ${resp.body()}")
        return resp.body()
    }

    fun put(path: String, body: Map<String, Any?>, query: Map<String, String> = emptyMap()): String {
        val jsonBody = mapToJson(body)
        val request = HttpRequest.newBuilder()
            .uri(URI.create(buildUrl(path, query)))
            .header("apikey", key)
            .header("Authorization", "Bearer $key")
            .header("Content-Type", "application/json")
            .header("Prefer", "return=representation")
            .method("PATCH", HttpRequest.BodyPublishers.ofString(jsonBody))
            .build()
        val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() >= 400) throw RuntimeException("Supabase PATCH $path: ${resp.statusCode()} ${resp.body()}")
        return resp.body()
    }

    fun delete(path: String, query: Map<String, String> = emptyMap()): String {
        val request = HttpRequest.newBuilder()
            .uri(URI.create(buildUrl(path, query)))
            .header("apikey", key)
            .header("Authorization", "Bearer $key")
            .DELETE()
            .build()
        val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() >= 400) throw RuntimeException("Supabase DELETE $path: ${resp.statusCode()} ${resp.body()}")
        return resp.body()
    }

    private fun mapToJson(map: Map<String, Any?>): String {
        val entries = map.entries.joinToString(",") { (k, v) ->
            val value = when (v) {
                null -> "null"
                is Boolean -> v.toString()
                is Number -> v.toString()
                is String -> "\"${v.replace("\"", "\\\"")}\""
                else -> "\"${v.toString().replace("\"", "\\\"")}\""
            }
            "\"$k\":$value"
        }
        return "{$entries}"
    }

    inline fun <reified T> parse(jsonStr: String): List<T> {
        return json.decodeFromString(ListSerializer(kotlinx.serialization.serializer<T>()), jsonStr)
    }

    fun parseMapList(jsonStr: String): List<Map<String, Any?>> {
        val element = json.parseToJsonElement(jsonStr) as JsonArray
        return element.map { (it as JsonObject).toMap() }
    }
}
