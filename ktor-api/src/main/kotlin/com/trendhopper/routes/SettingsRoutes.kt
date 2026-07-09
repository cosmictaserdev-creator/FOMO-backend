package com.trendhopper.routes

import com.trendhopper.models.*
import com.trendhopper.services.SupabaseClient
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.request.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Route.settingRoutes() {
    route("/settings") {
        get {
            val resp = SupabaseClient.get("settings", mapOf("select" to "key,value"))
            val body = SupabaseClient.parseMapList(resp)
            val settings = body.associate { it["key"]?.toString() to it["value"]?.toString() }
            call.respond(ApiResponse.ok(settings))
        }

        put {
            val request = call.receive<SettingValue>()
            val existing = SupabaseClient.get("settings", mapOf("select" to "key", "key" to "eq.${request.key}"))
            val exists = SupabaseClient.parseMapList(existing).isNotEmpty()
            if (exists) {
                SupabaseClient.put("settings", mapOf("value" to request.value), mapOf("key" to "eq.${request.key}"))
            } else {
                SupabaseClient.post("settings", mapOf("key" to request.key, "value" to request.value))
            }
            call.respond(ApiResponse.ok(mapOf("key" to request.key, "value" to request.value)))
        }
    }
}
