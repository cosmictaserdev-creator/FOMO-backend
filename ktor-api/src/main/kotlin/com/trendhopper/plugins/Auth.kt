package com.trendhopper.plugins

import io.ktor.server.application.*
import io.ktor.server.auth.*

fun Application.configureAuth() {
    val expectedToken = System.getenv("API_AUTH_TOKEN")
        ?: error("API_AUTH_TOKEN not set -- refusing to start with no API authentication configured")

    install(Authentication) {
        bearer("api-token") {
            authenticate { tokenCredential ->
                if (tokenCredential.token == expectedToken) UserIdPrincipal("local") else null
            }
        }
    }
}
