package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.sourceRoutes() {
    route("/sources") {
        get {
            val resp = SupabaseClient.get("sources_config", mapOf("select" to "id,name,enabled,params,created_at", "order" to "name.asc"))
            val body = SupabaseClient.parseMapList(resp)
            call.respond(ApiResponse.ok(body))
        }

        put("/{name}") {
            val name = call.parameters["name"] ?: return@put call.respond(HttpStatusCode.BadRequest, ApiResponse.error<Unit>("Missing name"))
            val request = call.receive<SourceUpdate>()

            val updateMap = mutableMapOf<String, Any?>()
            request.enabled?.let { updateMap["enabled"] = it }
            request.params?.let { updateMap["params"] = it.toString() }

            SupabaseClient.put("sources_config", updateMap, mapOf("name" to "eq.$name"))
            call.respond(ApiResponse.ok(mapOf("updated" to name)))
        }
    }
}
