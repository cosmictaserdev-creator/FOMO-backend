package com.trendhopper.models

import kotlinx.serialization.Serializable

@Serializable
data class FavoriteRequest(val item_id: String)

@Serializable
data class NoteContent(val content: String)

@Serializable
data class ChatRequest(val client_message_id: String, val message: String)

@Serializable
data class SettingValue(val key: String, val value: String)

@Serializable
data class TopicName(val name: String)

@Serializable
data class SourceUpdate(val enabled: Boolean? = null, val params: Map<String, kotlinx.serialization.json.JsonElement>? = null)
