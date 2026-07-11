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

        get("/test-ui") {
            val file = java.io.File("test-ui.html")
            if (file.exists()) {
                call.response.header(HttpHeaders.ContentType, "text/html; charset=utf-8")
                call.respondText(file.readText())
            } else {
                call.respondText("test-ui.html not found — rebuild it", status = HttpStatusCode.NotFound)
            }
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
