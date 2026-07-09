package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.noteRoutes() {
    route("/notes") {
        put("/{favorite_id}") {
            val favoriteId = call.parameters["favorite_id"] ?: return@put call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing favorite_id"))
            val request = call.receive<NoteContent>()

            val existing = SupabaseClient.get("notes", mapOf("select" to "id", "favorite_id" to "eq.$favoriteId"))
            val existingList = SupabaseClient.parseMapList(existing)

            val result = if (existingList.isNotEmpty()) {
                SupabaseClient.put("notes", mapOf("content" to request.content), mapOf("favorite_id" to "eq.$favoriteId"))
                existingList.first()
            } else {
                val resp = SupabaseClient.post("notes", mapOf("favorite_id" to favoriteId, "content" to request.content))
                val created = SupabaseClient.parseMapList(resp)
                created.firstOrNull() ?: mapOf("id" to "", "favorite_id" to favoriteId, "content" to request.content)
            }

            call.respond(ApiResponse.ok(result))
        }
    }
}
