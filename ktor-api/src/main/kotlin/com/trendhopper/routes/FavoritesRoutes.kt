package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.jsonPrimitive

fun Route.favoriteRoutes() {
    route("/favorites") {
        get {
            val resp = SupabaseClient.get("favorites", mapOf(
                "select" to "id,item_id,created_at,item:item_id(id,source,title,url,text_content,image_url,relevance_score,viral_score,matched_topic,llm_summary,llm_reasoning,published_at,fetched_at)",
                "order" to "created_at.desc",
            ))
            val favorites = SupabaseClient.parse<FavoriteResponse>(resp)
            if (favorites.isEmpty()) {
                return@get call.respond(ApiResponse.ok(favorites))
            }

            val idsFilter = "in.(${favorites.joinToString(",") { it.id }})"
            val notesResp = SupabaseClient.get("notes", mapOf("select" to "favorite_id", "favorite_id" to idsFilter))
            val favIdsWithNotes = SupabaseClient.parseJsonList(notesResp).mapNotNull { it["favorite_id"]?.jsonPrimitive?.content }.toSet()
            val chatResp = SupabaseClient.get("agent_chats", mapOf("select" to "favorite_id", "favorite_id" to idsFilter))
            val favIdsWithChat = SupabaseClient.parseJsonList(chatResp).mapNotNull { it["favorite_id"]?.jsonPrimitive?.content }.toSet()

            val enriched = favorites.map { fav ->
                fav.copy(has_notes = favIdsWithNotes.contains(fav.id), has_chat = favIdsWithChat.contains(fav.id))
            }
            call.respond(ApiResponse.ok(enriched))
        }

        post {
            val request = call.receive<FavoriteRequest>()
            try {
                val resp = SupabaseClient.post("favorites", mapOf("item_id" to request.item_id))
                SupabaseClient.put("items", mapOf("never_favorited" to false), mapOf("id" to "eq.${request.item_id}"))
                // Parse into a @Serializable type — returning a raw Map<String, Any?> here fails at
                // runtime with "Serializer for class 'ApiResponse' is not found".
                val created = SupabaseClient.parse<FavoriteResponse>(resp)
                val favorite = created.firstOrNull()
                    ?: return@post call.respond(HttpStatusCode.InternalServerError, ApiResponse.error<Unit>("Favorite was not returned by the database"))
                call.respond(HttpStatusCode.Created, ApiResponse.ok(favorite))
            } catch (e: Exception) {
                call.respond(HttpStatusCode.InternalServerError, ApiResponse.error<Unit>(e.message ?: "Failed to create favorite"))
            }
        }

        delete("/{id}") {
            val id = call.parameters["id"] ?: return@delete call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing id"))
            SupabaseClient.delete("favorites", mapOf("id" to "eq.$id"))
            call.respond(ApiResponse.ok(mapOf("deleted" to id)))
        }
    }
}
