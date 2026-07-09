package com.trendhopper.models

import kotlinx.serialization.Serializable

@Serializable
data class ApiResponse<T>(
    val success: Boolean,
    val data: T? = null,
    val error: String? = null,
) {
    companion object {
        fun <T> ok(data: T): ApiResponse<T> = ApiResponse(success = true, data = data)
        fun <T> error(message: String): ApiResponse<T> = ApiResponse(success = false, error = message)
    }
}

@Serializable
data class ItemResponse(
    val id: String,
    val source: String,
    val title: String,
    val url: String,
    val relevance_score: Int? = null,
    val viral_score: Double? = null,
    val matched_topic: String? = null,
    val llm_summary: String? = null,
    val published_at: String? = null,
    val fetched_at: String? = null,
    val is_favorited: Boolean = false,
)

@Serializable
data class FavoriteResponse(
    val id: String,
    val item_id: String,
    val created_at: String? = null,
    val has_notes: Boolean = false,
    val has_chat: Boolean = false,
    val item: ItemResponse? = null,
)

@Serializable
data class NoteResponse(
    val id: String,
    val favorite_id: String,
    val content: String,
    val updated_at: String? = null,
)

@Serializable
data class ChatMessage(
    val role: String,
    val content: String,
    val client_message_id: String? = null,
)

@Serializable
data class ChatThreadResponse(
    val id: String,
    val favorite_id: String,
    val messages: List<ChatMessage>,
)

@Serializable
data class StatsResponse(
    val total_items: Int,
    val total_favorites: Int,
    val avg_relevance: Double? = null,
    val per_source: List<SourceStat> = emptyList(),
)

@Serializable
data class SourceStat(
    val source: String,
    val count: Int,
)

@Serializable
data class CalendarResponse(
    val month: String,
    val days: Map<String, Int>,
)

@Serializable
data class SyncStatusResponse(
    val state: String,
    val last_sync_at: String? = null,
    val last_error_reason: String? = null,
)
