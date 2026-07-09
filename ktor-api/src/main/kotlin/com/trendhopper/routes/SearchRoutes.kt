package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.searchRoutes() {
    get("/search") {
        val q = call.request.queryParameters["q"] ?: return@get call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing q"))

        val itemsResp = SupabaseClient.get("items", mapOf(
            "select" to "id,source,title,url,relevance_score,viral_score,matched_topic,llm_summary,published_at,fetched_at",
            "or" to "(title.ilike.*$q*,llm_summary.ilike.*$q*)",
            "limit" to "50",
        ))
        val items = SupabaseClient.parse<ItemResponse>(itemsResp)

        val topicsResp = SupabaseClient.get("topics", mapOf(
            "select" to "name",
            "name" to "ilike.*$q*",
            "limit" to "10",
        ))
        val topics = SupabaseClient.parseMapList(topicsResp)

        val sourcesResp = SupabaseClient.get("sources_config", mapOf(
            "select" to "name,enabled",
            "name" to "ilike.*$q*",
            "limit" to "10",
        ))
        val sources = SupabaseClient.parseMapList(sourcesResp)

        call.respond(ApiResponse.ok(mapOf(
            "items" to items,
            "topics" to topics.map { it["name"] },
            "sources" to sources,
        )))
    }
}
