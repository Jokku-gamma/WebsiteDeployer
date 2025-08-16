// lib/main.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert'; // For JSON encoding/decoding

void main() {
  runApp(const JokkulabsCreatorApp());
}

class JokkulabsCreatorApp extends StatelessWidget {
  const JokkulabsCreatorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Jokkulabs Content Creator',
      theme: ThemeData(
        brightness: Brightness.dark, // Dark theme for a cool look
        primarySwatch: Colors.blueGrey,
        scaffoldBackgroundColor: const Color(0xFF0F002B), // Deep gradient start color
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0x66000000), // Semi-transparent black
          elevation: 0,
          centerTitle: true,
        ),
        cardTheme: CardThemeData(
          color: Colors.white.withOpacity(0.08), // Transparent card background
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16.0),
          ),
          elevation: 8,
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white.withOpacity(0.1),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
            borderSide: BorderSide.none,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12.0),
            borderSide: const BorderSide(color: Colors.blueAccent, width: 2.0),
          ),
          labelStyle: TextStyle(color: Colors.blueGrey[200]),
          hintStyle: TextStyle(color: Colors.blueGrey[400]),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            foregroundColor: Colors.white,
            backgroundColor: Colors.blueAccent,
            padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 15),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(30.0),
            ),
            textStyle: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            elevation: 10,
          ),
        ),
        textTheme: const TextTheme(
          headlineMedium: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          bodyLarge: TextStyle(color: Colors.white70),
          bodyMedium: TextStyle(color: Colors.white60),
          labelLarge: TextStyle(color: Colors.white),
        ),
      ),
      home: const LessonGeneratorScreen(),
    );
  }
}

class LessonGeneratorScreen extends StatefulWidget {
  const LessonGeneratorScreen({super.key});

  @override
  State<LessonGeneratorScreen> createState() => _LessonGeneratorScreenState();
}

class _LessonGeneratorScreenState extends State<LessonGeneratorScreen> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _courseIdController = TextEditingController(text: 'python');
  final TextEditingController _lessonTopicController = TextEditingController();
  final TextEditingController _aiPromptDetailsController = TextEditingController();
  final TextEditingController _targetDirectoryController = TextEditingController(text: 'courses/python/contents');
  final TextEditingController _geminiApiKeyController = TextEditingController();

  bool _isLoading = false;
  String? _message;
  bool _isError = false;

  // Base URL for your Python Flask backend
  static const String _backendBaseUrl = 'https://jokkulabsapi.onrender.com';

  Future<void> _generateLesson() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
      _message = null;
      _isError = false;
    });

    final String courseId = _courseIdController.text.trim();
    final String lessonTopic = _lessonTopicController.text.trim();
    final String aiPromptDetails = _aiPromptDetailsController.text.trim();
    final String targetDirectory = _targetDirectoryController.text.trim();
    final String geminiApiKey = _geminiApiKeyController.text.trim();

    final Map<String, String> requestBody = {
      'course_id': courseId,
      'lesson_topic': lessonTopic,
      'ai_prompt_details': aiPromptDetails,
      'target_directory': targetDirectory,
      'gemini_api_key': geminiApiKey,
    };

    try {
      final http.Response response = await http.post(
        Uri.parse('$_backendBaseUrl/generate_and_add_lesson'),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode(requestBody),
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> responseData = jsonDecode(response.body);
        setState(() {
          _message = 'Success! ${responseData['message']}\n'
                     'Filename: ${responseData['filename']}\n'
                     'GitHub URL: ${responseData['github_url']}';
          _isError = false;
        });
        _lessonTopicController.clear();
        _aiPromptDetailsController.clear();
      } else {
        final Map<String, dynamic> errorData = jsonDecode(response.body);
        setState(() {
          _message = 'Error (${response.statusCode}): ${errorData['error'] ?? 'Unknown error'}';
          _isError = true;
        });
      }
    } catch (e) {
      setState(() {
        _message = 'Network Error: Could not connect to the backend. Is it running at $_backendBaseUrl?\nError: $e';
        _isError = true;
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Jokkulabs Lesson Generator', style: TextStyle(color: Colors.white)),
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0x66000000), Color(0x33000000)], // Subtle header gradient
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
            ),
          ),
        ),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F002B), Color(0xFF2A0050), Color(0xFF4A005A)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(20.0),
            child: Card(
              margin: const EdgeInsets.symmetric(horizontal: 20.0),
              child: Padding(
                padding: const EdgeInsets.all(25.0),
                child: Form(
                  key: _formKey,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: <Widget>[
                      Text(
                        'Generate New Lesson Content',
                        style: Theme.of(context).textTheme.headlineMedium,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 30),
                      TextFormField(
                        controller: _courseIdController,
                        decoration: const InputDecoration(
                          labelText: 'Course ID (e.g., python, flutter, c)',
                          hintText: 'python',
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter a Course ID';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 20),
                      TextFormField(
                        controller: _lessonTopicController,
                        decoration: const InputDecoration(
                          labelText: 'Lesson Topic',
                          hintText: 'e.g., Python Variables and Operators',
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter a Lesson Topic';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 20),
                      TextFormField(
                        controller: _aiPromptDetailsController,
                        decoration: const InputDecoration(
                          labelText: 'AI Prompt Details (optional, but recommended)',
                          hintText: 'e.g., Explain basic variable types, assignment, and arithmetic operators with examples.',
                          alignLabelWithHint: true,
                        ),
                        maxLines: 5,
                      ),
                      const SizedBox(height: 20),
                      TextFormField(
                        controller: _targetDirectoryController,
                        decoration: const InputDecoration(
                          labelText: 'Target Directory in Repo',
                          hintText: 'e.g., courses/python/contents',
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter the target directory';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 20),
                      TextFormField(
                        controller: _geminiApiKeyController,
                        decoration: const InputDecoration(
                          labelText: 'Gemini API Key',
                          hintText: 'Enter your Gemini API Key',
                        ),
                        obscureText: true, // Hide the API key
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter your Gemini API Key';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 30),
                      _isLoading
                          ? const CircularProgressIndicator(color: Colors.blueAccent)
                          : ElevatedButton(
                              onPressed: _generateLesson,
                              child: const Text('Generate & Add Lesson'),
                            ),
                      const SizedBox(height: 20),
                      if (_message != null)
                        Text(
                          _message!,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: _isError ? Colors.redAccent : Colors.greenAccent,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
