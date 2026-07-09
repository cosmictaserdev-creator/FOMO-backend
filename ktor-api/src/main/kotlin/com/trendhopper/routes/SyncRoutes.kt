package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive

fun Route.syncRoutes() {
    route("/sync") {
        get("/status") {
            val resp = SupabaseClient.get("sync_log", mapOf(
                "select" to "status,last_error_reason,last_successful_sync_at,created_at",
                "order" to "created_at.desc",
                "limit" to "1",
            ))
            val rows = SupabaseClient.parseJsonList(resp)
            val latest = rows.firstOrNull()

            val state: String = when (latest?.get("status")?.jsonPrimitive?.contentOrNull) {
                "synced" -> "synced"
                "syncing" -> "syncing"
                "failed" -> "failed"
                "offline" -> "offline"
                else -> "offline"
            }

            call.respond(ApiResponse.ok(SyncStatusResponse(
                state = state,
                last_sync_at = latest?.get("created_at")?.jsonPrimitive?.contentOrNull,
                last_error_reason = latest?.get("last_error_reason")?.jsonPrimitive?.contentOrNull,
            )))
        }

        post("/retry") {
            // Only works when the pipeline is co-located on this machine (the bundled desktop
            // app scenario) -- PIPELINE_EXE_PATH is set by the GUI when it launches this
            // process. A Ktor deployment with no local pipeline (e.g. hosted standalone)
            // simply has no such env var and falls back to an informational response.
            val exePath = System.getenv("PIPELINE_EXE_PATH")
            if (exePath == null) {
                return@post call.respond(ApiResponse.ok(mapOf(
                    "message" to "No local pipeline is configured on this server. The next scheduled run will attempt collection again.",
                )))
            }

            val args = System.getenv("PIPELINE_EXE_ARGS")?.split("\u001F")?.filter { it.isNotBlank() } ?: emptyList()
            try {
                ProcessBuilder(listOf(exePath) + args).start()
                call.respond(ApiResponse.ok(mapOf(
                    "message" to "Retry triggered. Poll GET /sync/status to observe progress.",
                )))
            } catch (e: Exception) {
                call.respond(HttpStatusCode.InternalServerError, ApiResponse.error<Unit>("Failed to launch pipeline: ${e.message}"))
            }
        }
    }
}
