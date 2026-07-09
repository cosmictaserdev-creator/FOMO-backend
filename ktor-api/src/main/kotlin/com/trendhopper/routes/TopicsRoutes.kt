package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.topicRoutes() {
    route("/topics") {
        get {
            val resp = SupabaseClient.get("topics", mapOf("select" to "id,name,active,created_at", "order" to "name.asc"))
            val body = SupabaseClient.parseMapList(resp)
            call.respond(ApiResponse.ok(body))
        }

        post {
            val request = call.receive<TopicName>()
            try {
                val resp = SupabaseClient.post("topics", mapOf("name" to request.name))
                val created = SupabaseClient.parseMapList(resp)
                call.respond(HttpStatusCode.Created, ApiResponse.ok(created.firstOrNull()))
            } catch (e: Exception) {
                call.respond(HttpStatusCode.InternalServerError, ApiResponse.error<Unit>(e.message ?: "Failed to create topic"))
            }
        }

        delete("/{name}") {
            val name = call.parameters["name"] ?: return@delete call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing name"))
            SupabaseClient.delete("topics", mapOf("name" to "eq.$name"))
            call.respond(ApiResponse.ok(mapOf("deleted" to name)))
        }
    }
}
