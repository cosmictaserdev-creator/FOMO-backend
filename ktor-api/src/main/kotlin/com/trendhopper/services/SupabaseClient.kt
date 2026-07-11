package com.trendhopper.services

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.longOrNull
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

    suspend fun get(path: String, query: Map<String, String> = emptyMap()): String = withContext(Dispatchers.IO) {
        val request = HttpRequest.newBuilder()
            .uri(URI.create(buildUrl(path, query)))
            .header("apikey", key)
            .header("Authorization", "Bearer $key")
            .GET()
            .build()
        val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() >= 400) throw RuntimeException("Supabase GET $path: ${resp.statusCode()} ${resp.body()}")
        resp.body()
    }

    suspend fun post(path: String, body: Map<String, Any?>): String = withContext(Dispatchers.IO) {
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
        resp.body()
    }

    suspend fun put(path: String, body: Map<String, Any?>, query: Map<String, String> = emptyMap()): String = withContext(Dispatchers.IO) {
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
        resp.body()
    }

    suspend fun delete(path: String, query: Map<String, String> = emptyMap()): String = withContext(Dispatchers.IO) {
        val request = HttpRequest.newBuilder()
            .uri(URI.create(buildUrl(path, query)))
            .header("apikey", key)
            .header("Authorization", "Bearer $key")
            .DELETE()
            .build()
        val resp = client.send(request, HttpResponse.BodyHandlers.ofString())
        if (resp.statusCode() >= 400) throw RuntimeException("Supabase DELETE $path: ${resp.statusCode()} ${resp.body()}")
        resp.body()
    }

    // Uses the JSON library's own encoder rather than manual string concatenation -- the old
    // version only escaped `"`, so backslashes/newlines/control chars in user text (notes, chat
    // messages) produced malformed JSON sent to Supabase.
    private fun mapToJson(map: Map<String, Any?>): String {
        val obj = JsonObject(map.mapValues { (_, v) -> anyToJsonElement(v) })
        return json.encodeToString(JsonObject.serializer(), obj)
    }

    private fun anyToJsonElement(v: Any?): JsonElement = when (v) {
        null -> JsonNull
        is JsonElement -> v
        is Boolean -> JsonPrimitive(v)
        is Number -> JsonPrimitive(v)
        is Map<*, *> -> JsonObject(v.entries.associate { (k, value) -> k.toString() to anyToJsonElement(value) })
        is List<*> -> JsonArray(v.map { anyToJsonElement(it) })
        else -> JsonPrimitive(v.toString())
    }

    inline fun <reified T> parse(jsonStr: String): List<T> {
        return json.decodeFromString(ListSerializer(kotlinx.serialization.serializer<T>()), jsonStr)
    }

    // Unwraps a JsonElement into a plain Kotlin value so callers doing `.toString()` on the
    // result get the natural representation (e.g. "70", not "\"70\"") instead of re-serialized JSON.
    private fun unwrap(element: JsonElement): Any? = when (element) {
        is JsonNull -> null
        is JsonPrimitive -> if (element.isString) element.content else element.booleanOrNull ?: element.longOrNull ?: element.doubleOrNull ?: element.content
        is JsonArray -> element.map { unwrap(it) }
        is JsonObject -> element.mapValues { (_, v) -> unwrap(v) }
    }

    fun parseMapList(jsonStr: String): List<Map<String, Any?>> {
        val element = json.parseToJsonElement(jsonStr) as JsonArray
        return element.map { (it as JsonObject).mapValues { (_, v) -> unwrap(v) } }
    }

    fun parseJsonList(jsonStr: String): List<JsonObject> {
        val element = json.parseToJsonElement(jsonStr) as JsonArray
        return element.map { it as JsonObject }
    }
}
