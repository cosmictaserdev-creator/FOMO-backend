package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import java.time.Instant
import java.time.temporal.ChronoUnit

private suspend fun withFavoritedFlag(items: List<ItemResponse>): List<ItemResponse> {
    if (items.isEmpty()) return items
    val idsFilter = "in.(${items.joinToString(",") { it.id }})"
    val resp = SupabaseClient.get("favorites", mapOf("select" to "item_id", "item_id" to idsFilter))
    val favoritedIds = SupabaseClient.parseMapList(resp).mapNotNull { it["item_id"]?.toString() }.toSet()
    return items.map { it.copy(is_favorited = favoritedIds.contains(it.id)) }
}

fun Route.itemRoutes() {
    route("/items") {
        get {
            val feed = call.request.queryParameters["feed"] ?: "topics"
            val range = call.request.queryParameters["range"] ?: "week"
            val minRelevance = call.request.queryParameters["min_relevance"] ?: "0"

            val fromDate = when (range) {
                "day" -> Instant.now().minus(1, ChronoUnit.DAYS).toString()
                "month" -> Instant.now().minus(30, ChronoUnit.DAYS).toString()
                else -> Instant.now().minus(7, ChronoUnit.DAYS).toString()
            }

            // Order by recency so the freshest items are always in the returned window;
            // the client then re-ranks by a composite of relevance + recency + virality.
            // (Ordering by relevance_score alone buried fresh posts under week-old ones.)
            val order = if (feed == "general") "viral_score.desc" else "fetched_at.desc"
            val query = mutableMapOf(
                "select" to "id,source,title,url,text_content,image_url,relevance_score,viral_score,matched_topic,llm_summary,llm_reasoning,published_at,fetched_at",
                "relevance_score" to "gte.$minRelevance",
                "order" to order,
                "limit" to "150",
            )
            if (range != "all") {
                query["fetched_at"] = "gte.$fromDate"
            }

            val resp = SupabaseClient.get("items", query)
            val items = SupabaseClient.parse<ItemResponse>(resp)
            call.respond(ApiResponse.ok(withFavoritedFlag(items)))
        }

        get("/{id}") {
            val id = call.parameters["id"] ?: return@get call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing id"))
            val resp = SupabaseClient.get("items", mapOf(
                "select" to "id,source,title,url,text_content,image_url,relevance_score,viral_score,matched_topic,llm_summary,llm_reasoning,published_at,fetched_at",
                "id" to "eq.$id",
            ))
            val items = SupabaseClient.parse<ItemResponse>(resp)
            val item = items.firstOrNull() ?: return@get call.respond(HttpStatusCode.NotFound, ApiResponse.error<Unit>("Item not found"))
            call.respond(ApiResponse.ok(withFavoritedFlag(listOf(item)).first()))
        }
    }
}
