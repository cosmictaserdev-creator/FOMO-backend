package com.trendhopper.plugins

import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.plugins.cors.routing.*

fun Application.configureCORS() {
    install(CORS) {
        allowMethod(HttpMethod.Put)
        allowMethod(HttpMethod.Delete)
        allowHeader(HttpHeaders.ContentType)
        allowHeader(HttpHeaders.Authorization)
        // Bundled control-panel app and any local dev client talk to the API on localhost only.
        // Extend this list (don't reopen to anyHost()) if a real remote/mobile client ships.
        allowHost("localhost:${System.getenv("PORT") ?: "8080"}", schemes = listOf("http"))
        allowHost("127.0.0.1:${System.getenv("PORT") ?: "8080"}", schemes = listOf("http"))

    }
}
