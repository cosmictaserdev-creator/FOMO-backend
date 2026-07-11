package com.trendhopper.plugins

import io.ktor.server.application.*
import io.ktor.server.auth.*
import java.security.MessageDigest

fun Application.configureAuth() {
    val expectedToken = System.getenv("API_AUTH_TOKEN")
        ?: error("API_AUTH_TOKEN not set -- refusing to start with no API authentication configured")
    val expectedBytes = expectedToken.toByteArray()

    install(Authentication) {
        bearer("api-token") {
            authenticate { tokenCredential ->
                // Constant-time compare -- avoids leaking token bytes via response-time side channel.
                if (MessageDigest.isEqual(tokenCredential.token.toByteArray(), expectedBytes)) {
                    UserIdPrincipal("local")
                } else null
            }
        }
    }
}
