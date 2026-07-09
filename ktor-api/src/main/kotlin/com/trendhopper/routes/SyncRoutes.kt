package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.syncRoutes() {
    route("/sync") {
        get("/status") {
            val resp = SupabaseClient.get("sync_log", mapOf(
                "select" to "status,last_error_reason,last_successful_sync_at,created_at",
                "order" to "created_at.desc",
                "limit" to "1",
            ))
            val rows = SupabaseClient.parseMapList(resp)
            val latest = rows.firstOrNull()

            val state: String = when (latest?.get("status")?.toString()) {
                "synced" -> "synced"
                "syncing" -> "syncing"
                "failed" -> "failed"
                "offline" -> "offline"
                else -> "offline"
            }

            call.respond(ApiResponse.ok(SyncStatusResponse(
                state = state,
                last_sync_at = latest?.get("created_at")?.toString(),
                last_error_reason = latest?.get("last_error_reason")?.toString(),
            )))
        }

        post("/retry") {
            val resp = SupabaseClient.get("sync_log", mapOf(
                "select" to "status,last_error_reason,created_at",
                "order" to "created_at.desc",
                "limit" to "1",
            ))
            val latest = SupabaseClient.parseMapList(resp).firstOrNull()

            call.respond(ApiResponse.ok(mapOf(
                "message" to "Manual retry acknowledged. The next scheduled run will attempt collection again.",
                "last_attempt" to latest?.get("status"),
            )))
        }
    }
}
