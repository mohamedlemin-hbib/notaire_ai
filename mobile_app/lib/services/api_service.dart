import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static String baseUrl = kIsWeb
      ? "http://127.0.0.1:8000/api/v1"
      : (defaultTargetPlatform == TargetPlatform.android
          ? "http://10.0.2.2:8000/api/v1"
          : "http://127.0.0.1:8000/api/v1");

  static String baseOrigin = kIsWeb
      ? "http://127.0.0.1:8000"
      : (defaultTargetPlatform == TargetPlatform.android
          ? "http://10.0.2.2:8000"
          : "http://127.0.0.1:8000");

  static const _storage = FlutterSecureStorage();
  static String? _token;
  static String? _notaryName;
  static String? _userRole;

  static String? get notaryName => _notaryName;
  static bool get isAuthenticated => _token != null;
  static bool get isAdmin => _userRole == 'admin';

  static Future<void> init() async {
    _token = await _storage.read(key: 'auth_token');
    _notaryName = await _storage.read(key: 'notary_name');
    _userRole = await _storage.read(key: 'user_role');
    
    if (kDebugMode) {
      print("DEBUG: ApiService initialized. Token found: ${_token != null}, Role: $_userRole");
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
      _userRole = data['user']['role']?.toString();
      
      await _storage.write(key: 'auth_token', value: _token);
      await _storage.write(key: 'notary_name', value: _notaryName);
      await _storage.write(key: 'user_role', value: _userRole);
      
      return true;
    }
    return false;
  }

  static Future<void> logout() async {
    _token = null;
    _notaryName = null;
    _userRole = null;
    
    await _storage.delete(key: 'auth_token');
    await _storage.delete(key: 'notary_name');
    await _storage.delete(key: 'user_role');
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
      XFile vendeur, XFile acheteur, {String actType = "vente_immobilier"}) async {
    var uri = Uri.parse('$baseUrl/id-processing/from-id-cards');
    // Ajouter act_type comme paramètre de requête
    uri = uri.replace(queryParameters: {'act_type': actType});
    
    var request = http.MultipartRequest('POST', uri);
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

  // ── User Management ───────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getMe() async {
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: _getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    }
    throw Exception('Erreur lors de la récupération du profil');
  }

  static Future<bool> register(Map<String, dynamic> userData) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(userData),
    );
    return response.statusCode == 200;
  }

  static Future<List<dynamic>> getUsers() async {
    final response = await http.get(
      Uri.parse('$baseUrl/admin/users'),
      headers: _getHeaders(),
    );
    if (response.statusCode == 200) {
      return json.decode(utf8.decode(response.bodyBytes));
    }
    return [];
  }

  static Future<Map<String, dynamic>> createUser(Map<String, dynamic> userData) async {
    if (kDebugMode) print('DEBUG createUser: token=$_token, url=$baseUrl/admin/users');
    final response = await http.post(
      Uri.parse('$baseUrl/admin/users'),
      headers: _getHeaders(true),
      body: json.encode(userData),
    );
    if (kDebugMode) print('DEBUG createUser response: ${response.statusCode} ${response.body}');
    if (response.statusCode == 200 || response.statusCode == 201) {
      return {'success': true};
    }
    String errorMsg = 'Erreur ${response.statusCode}';
    try {
      final decoded = json.decode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded.containsKey('detail')) {
        errorMsg = decoded['detail'].toString();
      }
    } catch (_) {}
    return {'success': false, 'error': errorMsg};
  }

  static Future<bool> deleteUser(int userId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/admin/users/$userId'),
      headers: _getHeaders(),
    );
    return response.statusCode == 200;
  }

  static Future<Map<String, dynamic>> updateUser(int userId, Map<String, dynamic> userData) async {
    final response = await http.patch(
      Uri.parse('$baseUrl/admin/users/$userId'),
      headers: _getHeaders(true),
      body: json.encode(userData),
    );
    if (response.statusCode == 200) {
      return {'success': true};
    }
    String errorMsg = 'Erreur ${response.statusCode}';
    try {
      final decoded = json.decode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded.containsKey('detail')) {
        errorMsg = decoded['detail'].toString();
      }
    } catch (_) {}
    return {'success': false, 'error': errorMsg};
  }
}
