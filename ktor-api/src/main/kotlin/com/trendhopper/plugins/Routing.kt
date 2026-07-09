package com.trendhopper.plugins

import com.trendhopper.routes.*
import io.ktor.server.application.*
import io.ktor.server.routing.*

fun Application.configureRouting() {
    routing {
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
