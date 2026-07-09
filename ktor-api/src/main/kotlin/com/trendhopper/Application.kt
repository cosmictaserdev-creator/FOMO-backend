package com.trendhopper

import com.trendhopper.plugins.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*

fun main() {
    embeddedServer(Netty, port = System.getenv("PORT")?.toInt() ?: 8080, module = Application::module).start(wait = true)
}

fun Application.module() {
    configureSerialization()
    configureStatusPages()
    configureCORS()
    configureAuth()
    configureLogging()
    configureRouting()
}
