package com.trendhopper.plugins

import com.trendhopper.routes.*
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.auth.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun Application.configureRouting() {
    routing {
        get("/health") {
            call.respond(HttpStatusCode.OK, mapOf("status" to "ok"))
        }

        authenticate("api-token") {
            itemRoutes()
            favoriteRoutes()
            noteRoutes()
            agentRoutes()
            statsRoutes()
            searchRoutes()
            topicRoutes()
            sourceRoutes()
            settingRoutes()
            syncRoutes()
        }
    }
}
