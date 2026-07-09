package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.GroqClient
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*
import kotlinx.serialization.json.*

fun Route.agentRoutes() {
    route("/agent/chat") {
        get("/{favorite_id}") {
            val favoriteId = call.parameters["favorite_id"] ?: return@get call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing favorite_id"))

            val resp = SupabaseClient.get("agent_chats", mapOf(
                "select" to "id,favorite_id,messages",
                "favorite_id" to "eq.$favoriteId",
            ))
            val chats = SupabaseClient.parse<ChatThreadResponse>(resp)
            val thread = chats.firstOrNull()
                ?: return@get call.respond(ApiResponse.ok(ChatThreadResponse("", favoriteId, emptyList())))

            call.respond(ApiResponse.ok(thread))
        }

        post("/{favorite_id}") {
            val favoriteId = call.parameters["favorite_id"] ?: return@post call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing favorite_id"))
            val request = call.receive<ChatRequest>()

            val existingResp = SupabaseClient.get("agent_chats", mapOf("select" to "id,messages", "favorite_id" to "eq.$favoriteId"))
            val existingList = SupabaseClient.parseMapList(existingResp)
            val existingThread = existingList.firstOrNull()

            if (existingThread != null) {
                val messages = try {
                    Json.parseToJsonElement(existingThread["messages"]?.toString() ?: "[]").jsonArray
                } catch (_: Exception) { Json.parseToJsonElement("[]").jsonArray }

                val alreadyProcessed = messages.any { msg ->
                    msg.jsonObject["client_message_id"]?.jsonPrimitive?.content == request.client_message_id
                }
                if (alreadyProcessed) {
                    val thread = ChatThreadResponse(
                        id = existingThread["id"]?.toString() ?: "",
                        favorite_id = favoriteId,
                        messages = messages.map {
                            val obj = it.jsonObject
                            ChatMessage(
                                role = obj["role"]?.jsonPrimitive?.content ?: "",
                                content = obj["content"]?.jsonPrimitive?.content ?: "",
                                client_message_id = obj["client_message_id"]?.jsonPrimitive?.content,
                            )
                        },
                    )
                    return@post call.respond(ApiResponse.ok(thread))
                }
            }

            // Get item context
            val itemResp = SupabaseClient.get("items", mapOf("select" to "title,url,llm_summary", "id" to "eq.${favoriteId.split("-").first()}"))
            val itemContext = try {
                val items = SupabaseClient.parseMapList(itemResp)
                items.firstOrNull()?.let { "${it["title"] ?: ""} - ${it["llm_summary"] ?: it["url"] ?: ""}" } ?: ""
            } catch (_: Exception) { "" }

            // Build messages list
            val allMessages = mutableListOf<Map<String, String>>()
            allMessages.add(mapOf("role" to "system", "content" to "You are a helpful assistant discussing a saved news item: $itemContext. Keep responses concise (under 200 words) and reference the article when relevant."))

            if (existingThread != null) {
                val existing = try {
                    Json.parseToJsonElement(existingThread["messages"]?.toString() ?: "[]").jsonArray
                } catch (_: Exception) { Json.parseToJsonElement("[]").jsonArray }
                existing.forEach { msg ->
                    val obj = msg.jsonObject
                    allMessages.add(mapOf("role" to (obj["role"]?.jsonPrimitive?.content ?: "user"), "content" to (obj["content"]?.jsonPrimitive?.content ?: "")))
                }
            }
            allMessages.add(mapOf("role" to "user", "content" to request.message))

            // Call Groq
            val assistantContent = GroqClient.chat(allMessages)

            // Persist messages
            val newMessagesArray = buildJsonArray {
                if (existingThread != null) {
                    try {
                        val existing = Json.parseToJsonElement(existingThread["messages"]?.toString() ?: "[]").jsonArray
                        existing.forEach { add(it) }
                    } catch (_: Exception) {}
                }
                add(buildJsonObject {
                    put("role", "user")
                    put("content", request.message)
                    put("client_message_id", request.client_message_id)
                })
                add(buildJsonObject {
                    put("role", "assistant")
                    put("content", assistantContent)
                })
            }

            val threadId = existingThread?.get("id")?.toString()
            if (threadId != null) {
                SupabaseClient.put("agent_chats", mapOf("messages" to newMessagesArray.toString()), mapOf("id" to "eq.$threadId"))
            } else {
                SupabaseClient.post("agent_chats", mapOf("favorite_id" to favoriteId, "messages" to newMessagesArray.toString()))
            }

            val thread = ChatThreadResponse(
                id = threadId ?: "",
                favorite_id = favoriteId,
                messages = newMessagesArray.map { elem ->
                    val obj = elem.jsonObject
                    ChatMessage(
                        role = obj["role"]?.jsonPrimitive?.content ?: "",
                        content = obj["content"]?.jsonPrimitive?.content ?: "",
                        client_message_id = obj["client_message_id"]?.jsonPrimitive?.content,
                    )
                },
            )
            call.respond(ApiResponse.ok(thread))
        }
    }
}
