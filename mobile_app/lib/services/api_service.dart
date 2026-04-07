import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl =
      kIsWeb ? "http://localhost:8000/api/v1" : "http://10.0.2.2:8000/api/v1";
  static const String baseOrigin =
      kIsWeb ? "http://localhost:8000" : "http://10.0.2.2:8000";

  static const _storage = FlutterSecureStorage();
  static String? _token;
  static String? _notaryName;

  static String? get notaryName => _notaryName;
  static bool get isAuthenticated => _token != null;

  static Future<void> init() async {
    _token = await _storage.read(key: 'auth_token');
    _notaryName = await _storage.read(key: 'notary_name');
    if (kDebugMode) {
      print("DEBUG: ApiService initialized. Token found: ${_token != null}");
    }
  }

  static Map<String, String> _getHeaders([bool isJson = false]) {
    final Map<String, String> headers = {};
    if (_token != null) {
      headers['Authorization'] = 'Bearer $_token';
    }
    if (isJson) {
      headers['Content-Type'] = 'application/json';
    }
    return headers;
  }

  static String getFullUrl(String path) {
    if (path.isEmpty) return "";
    if (kDebugMode) print("DEBUG: getFullUrl input: '$path'");

    String result = path;
    if (result.contains("$baseOrigin$baseOrigin")) {
      result = result.replaceFirst(baseOrigin, "");
    }
    if (result.contains("://")) {
      if (kDebugMode) print("DEBUG: getFullUrl output (absolute): '$result'");
      return result;
    }
    final cleanPath = result.startsWith("/") ? result : "/$result";
    result = "$baseOrigin$cleanPath";
    if (kDebugMode) print("DEBUG: getFullUrl output (concatenated): '$result'");
    return result;
  }

  // ── Auth ──────────────────────────────────────────────────────────────────

  static Future<bool> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      body: {'username': username, 'password': password},
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _token = data['access_token'];
      _notaryName = data['user']['full_name'];
      await _storage.write(key: 'auth_token', value: _token);
      await _storage.write(key: 'notary_name', value: _notaryName);
      return true;
    }
    return false;
  }

  static Future<void> logout() async {
    _token = null;
    _notaryName = null;
    await _storage.delete(key: 'auth_token');
    await _storage.delete(key: 'notary_name');
  }

  // ── Chat Sessions ─────────────────────────────────────────────────────────

  static Future<List<dynamic>> getChatSessions() async {
    final response = await http.get(
      Uri.parse('$baseUrl/chat/sessions'),
      headers: _getHeaders(),
    );
    if (response.statusCode == 200) return json.decode(response.body);
    return [];
  }

  static Future<List<dynamic>> getChatMessages(int sessionId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/chat/sessions/$sessionId/messages'),
      headers: _getHeaders(),
    );
    if (response.statusCode == 200) return json.decode(response.body);
    return [];
  }

  static Future<Map<String, dynamic>> createChatSession(
      [String title = "Nouvelle discussion"]) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/sessions?title=${Uri.encodeComponent(title)}'),
      headers: _getHeaders(),
    );
    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception("Erreur lors de la création de la session");
  }

  static Future<void> addChatMessage(
      int sessionId, String role, String content,
      [String type = "text"]) async {
    await http.post(
      Uri.parse('$baseUrl/chat/messages'),
      headers: _getHeaders(true),
      body: json.encode({
        'session_id': sessionId,
        'role': role,
        'content': content,
        'message_type': type,
      }),
    );
  }

  /// Envoie un message et reçoit une vraie réponse de Gemini IA.
  static Future<Map<String, dynamic>> sendAiMessage(
      int sessionId, String message) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/ai-reply'),
      headers: _getHeaders(true),
      body: json.encode({
        'session_id': sessionId,
        'message': message,
      }),
    );
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    }
    
    // Tentative de décoder l'erreur JSON du backend
    String errMsg = response.body;
    try {
      final decoded = json.decode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded.containsKey('detail')) {
        errMsg = decoded['detail'];
      }
    } catch (_) {}
    
    throw Exception('Erreur IA (${response.statusCode}): $errMsg');
  }

  // ── Documents ─────────────────────────────────────────────────────────────

  static Future<List<dynamic>> getDocuments() async {
    final response = await http.get(
      Uri.parse('$baseUrl/documents/list'),
      headers: _getHeaders(),
    );
    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception('Erreur lors de la récupération des documents');
  }

  // ── ID Cards & Acte de Vente ──────────────────────────────────────────────

  static Future<Map<String, dynamic>> sendIdCards(
      XFile vendeur, XFile acheteur) async {
    var request = http.MultipartRequest(
        'POST', Uri.parse('$baseUrl/id-processing/from-id-cards'));
    request.headers.addAll(_getHeaders());

    if (kIsWeb) {
      request.files.add(http.MultipartFile.fromBytes(
          'vendeur_id', await vendeur.readAsBytes(),
          filename: vendeur.name));
      request.files.add(http.MultipartFile.fromBytes(
          'acheteur_id', await acheteur.readAsBytes(),
          filename: acheteur.name));
    } else {
      request.files
          .add(await http.MultipartFile.fromPath('vendeur_id', vendeur.path));
      request.files.add(
          await http.MultipartFile.fromPath('acheteur_id', acheteur.path));
    }

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    }
    
    String errMsg = response.body;
    try {
      final decoded = json.decode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded.containsKey('detail')) {
        errMsg = decoded['detail'];
      }
    } catch (_) {}
    
    throw Exception('Erreur de génération : $errMsg');
  }

  /// Complète un acte avec les champs manquants et régénère le PDF.
  static Future<Map<String, dynamic>> completeAct(
      int documentId, Map<String, String> data) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/id-processing/complete/$documentId'),
      headers: _getHeaders(true),
      body: json.encode(data),
    );
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    }
    
    String errMsg = response.body;
    try {
      final decoded = json.decode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded.containsKey('detail')) {
        errMsg = decoded['detail'];
      }
    } catch (_) {}
    
    throw Exception('Erreur lors de la complétion : $errMsg');
  }

  // ── Voice ─────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> sendVoiceMessage(String path) async {
    var request = http.MultipartRequest(
        'POST', Uri.parse('$baseUrl/multimodal/voice-to-text'));
    request.headers.addAll(_getHeaders());
    request.files.add(await http.MultipartFile.fromPath('file', path));

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception('Erreur lors de la transcription');
  }

  // ── Admin ─────────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> uploadTemplate(
      XFile file, String actType) async {
    var request = http.MultipartRequest(
        'POST', Uri.parse('$baseUrl/admin/upload-template'));
    request.headers.addAll(_getHeaders());
    request.fields['act_type'] = actType;

    if (kIsWeb) {
      request.files.add(http.MultipartFile.fromBytes(
          'file', await file.readAsBytes(),
          filename: file.name));
    } else {
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
    }

    var streamedResponse = await request.send();
    var response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) return json.decode(response.body);
    throw Exception('Erreur lors de l\'upload du modèle : ${response.body}');
  }
}
