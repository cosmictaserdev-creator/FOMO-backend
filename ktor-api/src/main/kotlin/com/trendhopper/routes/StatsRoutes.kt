package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import java.time.Instant
import java.time.YearMonth
import java.time.temporal.ChronoUnit

fun Route.statsRoutes() {
    get("/stats") {
        val range = call.request.queryParameters["range"] ?: "week"

        val fromDate = when (range) {
            "day" -> Instant.now().minus(1, ChronoUnit.DAYS).toString()
            "month" -> Instant.now().minus(30, ChronoUnit.DAYS).toString()
            else -> Instant.now().minus(7, ChronoUnit.DAYS).toString()
        }

        val itemsResp = SupabaseClient.get("items", mapOf(
            "select" to "id,source",
            "fetched_at" to "gte.$fromDate",
        ))
        val items = SupabaseClient.parseMapList(itemsResp)

        val perSource = items
            .groupBy { it["source"]?.toString() ?: "unknown" }
            .map { SourceStat(it.key, it.value.size) }
            .sortedByDescending { it.count }

        val favoritesResp = SupabaseClient.get("favorites", mapOf("select" to "id"))
        val favorites = SupabaseClient.parseMapList(favoritesResp)

        val stats = StatsResponse(
            total_items = items.size,
            total_favorites = favorites.size,
            avg_relevance = null,
            per_source = perSource,
        )

        call.respond(ApiResponse.ok(stats))
    }

    get("/calendar") {
        val month = call.request.queryParameters["month"] ?: YearMonth.now().toString()

        val monthStart = "$month-01"
        val nextMonth = YearMonth.parse(month).plusMonths(1).atDay(1).toString()
        val resp = SupabaseClient.get("items", mapOf(
            "select" to "fetched_at",
            "and" to "(fetched_at.gte.$monthStart,fetched_at.lt.$nextMonth)",
            "limit" to "1000",
        ))
        val items = SupabaseClient.parseMapList(resp)
        val days = items
            .mapNotNull { it["fetched_at"]?.toString()?.substringBefore("T") }
            .groupingBy { it }
            .eachCount()

        call.respond(ApiResponse.ok(CalendarResponse(month, days)))
    }
}
