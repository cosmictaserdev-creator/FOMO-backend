package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

// PostgREST treats \,.():  as filter-grammar syntax inside or()/ilike values, so a raw search
// term containing them (e.g. "),id.neq.0--") could alter or extend the intended filter. Escaping
// them with a backslash keeps the value literal per PostgREST's own escaping rules.
private val POSTGREST_RESERVED = Regex("""[\\,.()]""")

private fun escapePostgrestValue(raw: String): String =
    raw.replace(POSTGREST_RESERVED) { "\\${it.value}" }

fun Route.searchRoutes() {
    get("/search") {
        val qRaw = call.request.queryParameters["q"] ?: return@get call.respond(HttpStatusCode.BadRequest, SearchApiResponse(success = false, error = "Missing q"))
        val q = escapePostgrestValue(qRaw)

        val itemsResp = SupabaseClient.get("items", mapOf(
            "select" to "id,source,title,url,text_content,image_url,relevance_score,viral_score,matched_topic,llm_summary,llm_reasoning,published_at,fetched_at",
            "or" to "(title.ilike.*$q*,llm_summary.ilike.*$q*,text_content.ilike.*$q*)",
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
        val rawSources = SupabaseClient.parseMapList(sourcesResp)

        call.respond(SearchApiResponse(success = true, data = SearchResponse(
            items = items,
            topics = topics.mapNotNull { it["name"]?.toString() },
            sources = rawSources.map { src ->
                mapOf(
                    "name" to (src["name"]?.toString() ?: ""),
                    "enabled" to (src["enabled"]?.toString() ?: "false"),
                )
            },
        )))
    }
}
