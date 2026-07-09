package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import java.time.Instant
import java.time.temporal.ChronoUnit

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

            val query = mutableMapOf(
                "select" to "id,source,title,url,relevance_score,viral_score,matched_topic,llm_summary,published_at,fetched_at",
                "relevance_score" to "gte.$minRelevance",
                "order" to if (feed == "general") "viral_score.desc" else "relevance_score.desc",
                "limit" to "100",
            )
            if (range != "all") {
                query["fetched_at"] = "gte.$fromDate"
            }

            val resp = SupabaseClient.get("items", query)
            val items = SupabaseClient.parse<ItemResponse>(resp)
            call.respond(ApiResponse.ok(items))
        }

        get("/{id}") {
            val id = call.parameters["id"] ?: return@get call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing id"))
            val resp = SupabaseClient.get("items", mapOf(
                "select" to "id,source,title,url,relevance_score,viral_score,matched_topic,llm_summary,published_at,fetched_at",
                "id" to "eq.$id",
            ))
            val items = SupabaseClient.parse<ItemResponse>(resp)
            val item = items.firstOrNull() ?: return@get call.respond(HttpStatusCode.NotFound, ApiResponse.error<Unit>("Item not found"))
            call.respond(ApiResponse.ok(item))
        }
    }
}
