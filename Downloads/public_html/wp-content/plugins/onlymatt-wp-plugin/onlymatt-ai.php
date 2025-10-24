<?php
/**
 * Plugin Name: ONLYMATT AI Assistant
 * Plugin URI: https://om43.com
 * Description: Interface d'administration pour l'assistant AI ONLYMATT avec intégration Turso
 * Version: 1.0.0
 * Author: ONLYMATT
 * License: GPL v2 or later
 * Text Domain: onlymatt-ai
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Define constants
define('ONLYMATT_AI_VERSION', '1.0.0');
define('ONLYMATT_AI_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('ONLYMATT_AI_PLUGIN_URL', plugin_dir_url(__FILE__));

// Main plugin class
class OnlyMatt_AI_Plugin {

    public function __construct() {
        $this->init_hooks();
    }

    private function init_hooks() {
        add_action('init', array($this, 'init'));
        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_scripts'));
        add_action('wp_enqueue_scripts', array($this, 'enqueue_frontend_scripts'));

        // AJAX handlers
        add_action('wp_ajax_onlymatt_chat', array($this, 'handle_chat_ajax'));
        add_action('wp_ajax_onlymatt_save_memory', array($this, 'handle_save_memory_ajax'));
        add_action('wp_ajax_onlymatt_get_tasks', array($this, 'handle_get_tasks_ajax'));
        add_action('wp_ajax_onlymatt_create_task', array($this, 'handle_create_task_ajax'));
        add_action('wp_ajax_onlymatt_save_settings', array($this, 'handle_save_settings_ajax'));

        // Shortcodes
        add_shortcode('onlymatt_chat', array($this, 'chat_shortcode'));
        add_shortcode('onlymatt_admin', array($this, 'admin_shortcode'));
        add_shortcode('onlymatt_web_builder', array($this, 'web_builder_shortcode'));
        add_shortcode('onlymatt_hey_hi', array($this, 'hey_hi_shortcode'));

        // REST API
        add_action('rest_api_init', array($this, 'register_rest_routes'));
    }

    public function init() {
        // Load textdomain
        load_plugin_textdomain('onlymatt-ai', false, dirname(plugin_basename(__FILE__)) . '/languages/');
    }

    public function add_admin_menu() {
        add_menu_page(
            'ONLYMATT AI',
            'ONLYMATT AI',
            'manage_options',
            'onlymatt-ai',
            array($this, 'admin_page'),
            'dashicons-robot',
            30
        );

        add_submenu_page(
            'onlymatt-ai',
            'Chat',
            'Chat',
            'manage_options',
            'onlymatt-ai-chat',
            array($this, 'chat_page')
        );

        add_submenu_page(
            'onlymatt-ai',
            'Tâches',
            'Tâches',
            'manage_options',
            'onlymatt-ai-tasks',
            array($this, 'tasks_page')
        );

        add_submenu_page(
            'onlymatt-ai',
            'Paramètres',
            'Paramètres',
            'manage_options',
            'onlymatt-ai-settings',
            array($this, 'settings_page')
        );
    }

    public function enqueue_admin_scripts($hook) {
        if (strpos($hook, 'onlymatt-ai') === false) {
            return;
        }

        wp_enqueue_script('onlymatt-admin-js', ONLYMATT_AI_PLUGIN_URL . 'assets/js/admin.js', array('jquery'), ONLYMATT_AI_VERSION, true);
        wp_enqueue_style('onlymatt-admin-css', ONLYMATT_AI_PLUGIN_URL . 'assets/css/admin.css', array(), ONLYMATT_AI_VERSION);

        wp_localize_script('onlymatt-admin-js', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
            'admin_key' => get_option('onlymatt_admin_key', 'test_key')
        ));
    }

    public function enqueue_frontend_scripts() {
        wp_enqueue_script('onlymatt-frontend-js', ONLYMATT_AI_PLUGIN_URL . 'assets/js/frontend.js', array('jquery'), ONLYMATT_AI_VERSION, true);
        wp_enqueue_style('onlymatt-frontend-css', ONLYMATT_AI_PLUGIN_URL . 'assets/css/frontend.css', array(), ONLYMATT_AI_VERSION);

        wp_localize_script('onlymatt-frontend-js', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
            'admin_key' => get_option('onlymatt_admin_key', 'test_key')
        ));
    }

    // Admin pages
    public function admin_page() {
        wp_localize_script('onlymatt-admin-js', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com')
        ));
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/admin-dashboard.php';
    }

    public function chat_page() {
        wp_localize_script('onlymatt-admin-js', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
            'admin_key' => get_option('onlymatt_admin_key', 'test_key')
        ));
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/admin-chat.php';
    }

    public function tasks_page() {
        wp_localize_script('onlymatt-admin-js', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
            'admin_key' => get_option('onlymatt_admin_key', 'test_key')
        ));
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/admin-tasks.php';
    }

    public function settings_page() {
        wp_localize_script('onlymatt-admin-js', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
            'admin_key' => get_option('onlymatt_admin_key', 'test_key')
        ));
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/admin-settings.php';
    }

    // Shortcodes
    public function chat_shortcode($atts) {
        // Ensure frontend scripts are loaded
        if (!wp_script_is('onlymatt-frontend-js', 'enqueued')) {
            wp_enqueue_script('onlymatt-frontend-js');
            wp_enqueue_style('onlymatt-frontend-css');
            wp_localize_script('onlymatt-frontend-js', 'onlymatt_ajax', array(
                'ajax_url' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('onlymatt_nonce'),
                'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
                'admin_key' => get_option('onlymatt_admin_key', 'test_key')
            ));
        }

        ob_start();
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/frontend-chat.php';
        return ob_get_clean();
    }

    public function hey_hi_shortcode($atts) {
        if (!wp_script_is('jquery', 'enqueued')) {
            wp_enqueue_script('jquery');
        }

        wp_localize_script('jquery', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'site_info' => $this->get_site_knowledge()
        ));

        ob_start();
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/hey-hi-sphere.php';
        return ob_get_clean();
    }

    public function admin_shortcode($atts) {
        if (!current_user_can('manage_options')) {
            return '<p>Vous n\'avez pas les permissions nécessaires pour accéder à cette fonctionnalité.</p>';
        }

        // Ensure admin scripts are loaded
        if (!wp_script_is('onlymatt-admin-js', 'enqueued')) {
            wp_enqueue_script('onlymatt-admin-js');
            wp_enqueue_style('onlymatt-admin-css');
            wp_localize_script('onlymatt-admin-js', 'onlymatt_ajax', array(
                'ajax_url' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('onlymatt_nonce'),
                'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
                'admin_key' => get_option('onlymatt_admin_key', 'test_key')
            ));
        }

        ob_start();
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/frontend-admin.php';
        return ob_get_clean();
    }

    public function web_builder_shortcode($atts) {
        // Only allow editors / admins to access the web builder
        if (!current_user_can('edit_pages')) {
            return '<p>Vous n\'avez pas les permissions nécessaires pour accéder au Web Builder. Connectez-vous en tant qu\'éditeur ou administrateur.</p>';
        }

        // Ensure frontend scripts are loaded
        if (!wp_script_is('onlymatt-frontend-js', 'enqueued')) {
            wp_enqueue_script('onlymatt-frontend-js');
            wp_enqueue_style('onlymatt-frontend-css');
            wp_localize_script('onlymatt-frontend-js', 'onlymatt_ajax', array(
                'ajax_url' => admin_url('admin-ajax.php'),
                'nonce' => wp_create_nonce('onlymatt_nonce'),
                'api_base' => get_option('onlymatt_api_base', 'https://your-app.onrender.com'),
                'admin_key' => get_option('onlymatt_admin_key', 'test_key')
            ));
        }

        // Also provide site info and ensure jQuery is available for the embedded Hey Hi helper
        if (!wp_script_is('jquery', 'enqueued')) {
            wp_enqueue_script('jquery');
        }

        wp_localize_script('jquery', 'onlymatt_ajax', array(
            'ajax_url' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('onlymatt_nonce'),
            'site_info' => $this->get_site_knowledge()
        ));

        ob_start();
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/web-builder.php';

        // Include the Hey Hi helper inside the builder so editors can interact with it while composing
        // This will render the helper UI (floating or inline depending on its template)
        include ONLYMATT_AI_PLUGIN_DIR . 'templates/hey-hi-sphere.php';

        return ob_get_clean();
    }

    public function get_site_knowledge() {
        // Collect comprehensive site information
        $site_info = array(
            'site_title' => get_bloginfo('name'),
            'site_description' => get_bloginfo('description'),
            'site_url' => get_site_url(),
            'current_page' => array(
                'title' => get_the_title(),
                'url' => get_permalink(),
                'type' => get_post_type()
            ),
            'main_pages' => array(),
            'menu_structure' => array()
        );

        // Get main pages
        $main_pages = get_pages(array(
            'sort_column' => 'menu_order',
            'sort_order' => 'asc',
            'parent' => 0
        ));

        foreach ($main_pages as $page) {
            $site_info['main_pages'][] = array(
                'title' => $page->post_title,
                'url' => get_permalink($page->ID),
                'excerpt' => wp_trim_words($page->post_excerpt ?: $page->post_content, 20)
            );
        }

        // Get menu structure
        $menus = wp_get_nav_menus();
        foreach ($menus as $menu) {
            $menu_items = wp_get_nav_menu_items($menu->term_id);
            $site_info['menu_structure'][$menu->name] = array();

            foreach ($menu_items as $item) {
                $site_info['menu_structure'][$menu->name][] = array(
                    'title' => $item->title,
                    'url' => $item->url,
                    'description' => $item->description
                );
            }
        }

        return $site_info;
    }

        // AJAX handlers
    public function handle_chat_ajax() {
        check_ajax_referer('onlymatt_nonce', 'nonce');

        $message = sanitize_text_field($_POST['message']);
        $persona = sanitize_text_field($_POST['persona'] ?? get_option('onlymatt_default_persona', 'general_assistant'));
        $api_base = get_option('onlymatt_api_base', 'https://onlymatt-gateway.onrender.com');

        // Get persona configuration
        $personas = get_option('onlymatt_ai_personas', array());
        $system_prompt = isset($personas[$persona]['system_prompt']) ? $personas[$persona]['system_prompt'] : '';

        // Build messages array with system prompt if available
        $messages = array();
        if (!empty($system_prompt)) {
            $messages[] = array('role' => 'system', 'content' => $system_prompt);
        }
        $messages[] = array('role' => 'user', 'content' => $message);

        $response = wp_remote_post($api_base . '/ai/chat', array(
            'body' => json_encode(array(
                'messages' => $messages,
                'model' => 'llama-3.3-70b-versatile',
                'temperature' => 0.7
            )),
            'headers' => array(
                'Content-Type' => 'application/json',
            ),
            'timeout' => 60 // Increased timeout for complex tasks
        ));

        if (is_wp_error($response)) {
            wp_send_json_error('Erreur de connexion à l\'API');
        } else {
            $body = wp_remote_retrieve_body($response);
            $data = json_decode($body, true);

            // Add persona info to response
            if ($data && isset($data['response'])) {
                $data['persona'] = $persona;
                $data['persona_name'] = $personas[$persona]['name'] ?? $persona;
            }

            wp_send_json_success($data);
        }
    }

    public function handle_save_memory_ajax() {
        check_ajax_referer('onlymatt_nonce', 'nonce');

        $user_id = sanitize_text_field($_POST['user_id']);
        $key = sanitize_text_field($_POST['key']);
        $value = sanitize_textarea_field($_POST['value']);
        $api_base = get_option('onlymatt_api_base', 'https://your-app.onrender.com');

        $response = wp_remote_post($api_base . '/ai/memory/remember', array(
            'body' => json_encode(array(
                'user_id' => $user_id,
                'persona' => 'wp_assistant',
                'key' => $key,
                'value' => $value
            )),
            'headers' => array(
                'Content-Type' => 'application/json',
            ),
            'timeout' => 15
        ));

        if (is_wp_error($response)) {
            wp_send_json_error('Erreur de sauvegarde');
        } else {
            wp_send_json_success('Mémoire sauvegardée');
        }
    }

    public function handle_get_tasks_ajax() {
        check_ajax_referer('onlymatt_nonce', 'nonce');

        $api_base = get_option('onlymatt_api_base', 'https://your-app.onrender.com');

        $response = wp_remote_get($api_base . '/admin/tasks', array(
            'headers' => array(
                'X-OM-Key' => get_option('onlymatt_admin_key', 'test_key'),
            ),
            'timeout' => 15
        ));

        if (is_wp_error($response)) {
            wp_send_json_error('Erreur de récupération');
        } else {
            $body = wp_remote_retrieve_body($response);
            $data = json_decode($body, true);
            wp_send_json_success($data);
        }
    }

    public function handle_create_task_ajax() {
        check_ajax_referer('onlymatt_nonce', 'nonce');

        $title = sanitize_text_field($_POST['title']);
        $description = sanitize_textarea_field($_POST['description']);
        $priority = sanitize_text_field($_POST['priority']);
        $api_base = get_option('onlymatt_api_base', 'https://your-app.onrender.com');

        $response = wp_remote_post($api_base . '/admin/tasks', array(
            'body' => json_encode(array(
                'title' => $title,
                'description' => $description,
                'priority' => $priority
            )),
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-OM-Key' => get_option('onlymatt_admin_key', 'test_key'),
            ),
            'timeout' => 15
        ));

        if (is_wp_error($response)) {
            wp_send_json_error('Erreur de création');
        } else {
            wp_send_json_success('Tâche créée');
        }
    }

    public function handle_save_settings_ajax() {
        check_ajax_referer('onlymatt_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error('Insufficient permissions');
        }

        $settings = json_decode(stripslashes($_POST['settings']), true);

        if (!$settings) {
            wp_send_json_error('Invalid settings data');
        }

        // Save settings
        update_option('onlymatt_api_base', sanitize_url($settings['api_base'] ?? ''));
        update_option('onlymatt_admin_key', sanitize_text_field($settings['admin_key'] ?? ''));
        update_option('onlymatt_max_memory', intval($settings['max_memory'] ?? 100));
        update_option('onlymatt_enable_logging', $settings['enable_logging'] ? '1' : '0');
        update_option('onlymatt_enable_widget', $settings['enable_widget'] ? '1' : '0');

        wp_send_json_success('Settings saved');
    }

    // REST API routes
    public function register_rest_routes() {
        register_rest_route('onlymatt/v1', '/chat', array(
            'methods' => 'POST',
            'callback' => array($this, 'rest_chat'),
            'permission_callback' => '__return_true'
        ));

        register_rest_route('onlymatt/v1', '/memory', array(
            'methods' => 'POST',
            'callback' => array($this, 'rest_save_memory'),
            'permission_callback' => '__return_true'
        ));

        register_rest_route('onlymatt/v1', '/tasks', array(
            'methods' => 'GET',
            'callback' => array($this, 'rest_get_tasks'),
            'permission_callback' => '__return_true'
        ));
    }

    public function rest_chat($request) {
        $message = $request->get_param('message');
        $api_base = get_option('onlymatt_api_base', 'https://your-app.onrender.com');

        $response = wp_remote_post($api_base . '/ai/chat', array(
            'body' => json_encode(array('messages' => array(array('role' => 'user', 'content' => $message)))),
            'headers' => array('Content-Type' => 'application/json'),
            'timeout' => 30
        ));

        if (is_wp_error($response)) {
            return new WP_Error('api_error', 'Erreur de connexion', array('status' => 500));
        }

        $body = wp_remote_retrieve_body($response);
        return json_decode($body);
    }

    public function rest_save_memory($request) {
        $params = $request->get_params();
        $api_base = get_option('onlymatt_api_base', 'https://your-app.onrender.com');

        $response = wp_remote_post($api_base . '/ai/memory/remember', array(
            'body' => json_encode($params),
            'headers' => array('Content-Type' => 'application/json'),
            'timeout' => 15
        ));

        if (is_wp_error($response)) {
            return new WP_Error('api_error', 'Erreur de sauvegarde', array('status' => 500));
        }

        return array('success' => true);
    }

    public function rest_get_tasks($request) {
        $api_base = get_option('onlymatt_api_base', 'https://your-app.onrender.com');

        $response = wp_remote_get($api_base . '/admin/tasks', array(
            'headers' => array(
                'X-OM-Key' => get_option('onlymatt_admin_key', 'test_key'),
            ),
            'timeout' => 15
        ));

        if (is_wp_error($response)) {
            return new WP_Error('api_error', 'Erreur de récupération', array('status' => 500));
        }

        $body = wp_remote_retrieve_body($response);
        return json_decode($body);
    }
}

// Initialize plugin
new OnlyMatt_AI_Plugin();

// Activation hook
register_activation_hook(__FILE__, 'onlymatt_ai_activate');
function onlymatt_ai_activate() {
        // Set default options
    add_option('onlymatt_api_base', 'https://onlymatt-gateway.onrender.com');
    add_option('onlymatt_admin_key', '64b29ac4e96c12e23c1a58f93ad1509e');

    // Set default AI personas
    add_option('onlymatt_ai_personas', array(
        'web_developer' => array(
            'name' => 'Web Developer',
            'description' => 'Spécialisé dans la création de sites web',
            'system_prompt' => 'Tu es un développeur web expert. Ta mission principale est de construire des sites web complets en analysant les données fournies par l\'utilisateur, en consultant des sites web pour t\'informer et en ajustant le design selon les meilleures pratiques.

RÈGLES IMPORTANTES :
1. ANALYSE : Commence toujours par analyser les données fournies (contenu, structure, exigences)
2. RECHERCHE : Consulte des sites web similaires pour t\'inspirer du design et des fonctionnalités
3. DESIGN : Adapte le look selon les tendances actuelles et les besoins spécifiques
4. CODE : Génère du code HTML/CSS/JS propre, responsive et optimisé
5. STRUCTURE : Organise le contenu de manière logique et user-friendly

POUR CHAQUE PROJET :
- Analyse les données et exigences
- Recherche des références visuelles
- Propose une structure de site
- Génère le code complet avec commentaires
- Explique tes choix de design

UTILISE TOUJOURS :
- HTML5 sémantique
- CSS3 moderne avec Flexbox/Grid
- JavaScript vanilla (pas de frameworks lourds)
- Design responsive mobile-first
- Accessibilité WCAG
- Performance optimisée

FORMAT DE RÉPONSE :
1. 📊 ANALYSE DES DONNÉES
2. 🔍 RECHERCHE ET INSPIRATION
3. 🎨 CONCEPT ET STRUCTURE
4. 💻 CODE GÉNÉRÉ
5. 📝 EXPLICATIONS ET RECOMMANDATIONS'
        ),
        'general_assistant' => array(
            'name' => 'Assistant Général',
            'description' => 'Assistant IA polyvalent',
            'system_prompt' => 'Tu es un assistant IA helpful et polyvalent. Tu aides les utilisateurs avec diverses tâches de manière professionnelle et efficace.'
        ),
        'site_guide' => array(
            'name' => 'Site Guide',
            'description' => 'Guide IA qui connaît parfaitement le site web',
            'system_prompt' => 'Tu es un guide IA intelligent qui connaît parfaitement ce site web. Ta mission est d\'aider les visiteurs à naviguer, comprendre et utiliser le site de manière optimale.

CONNAISSANCES DU SITE :
- Tu as accès aux informations complètes du site (pages, menus, structure)
- Tu sais exactement où trouver chaque information
- Tu comprends la hiérarchie et l\'organisation du contenu

COMPORTEMENT :
1. SOIS ACCUEILLANT : Commence toujours par un message amical
2. SOIS CONTEXTUEL : Adapte tes réponses selon la page actuelle
3. SOIS PRÉCIS : Donne des liens et directions claires
4. SOIS PROACTIF : Anticipe les besoins des utilisateurs
5. SOIS BREF : Réponds de manière concise mais complète

FONCTIONS PRINCIPALES :
- 🧭 GUIDER la navigation sur le site
- 🔍 AIDER à trouver des informations spécifiques
- 📞 FACILITER les contacts et interactions
- ❓ RÉPONDRE aux questions générales
- 🎯 Orienter vers les bonnes sections

RÈGLES DE RÉPONSE :
- Utilise des emojis appropriés pour rendre les réponses engageantes
- Mentionne toujours les pages/sections pertinentes
- Propose des actions concrètes quand possible
- Réponds en français de manière naturelle
- Si tu ne sais pas quelque chose, dis-le et propose des alternatives

FORMAT :
- Messages courts et digestes
- Liens clairs vers les pages importantes
- Suggestions d\'actions pour l\'utilisateur'
        )
    ));

    // Set default persona
    add_option('onlymatt_default_persona', 'web_developer');

    // Create necessary directories
    $dirs = array(
        ONLYMATT_AI_PLUGIN_DIR . 'assets/css',
        ONLYMATT_AI_PLUGIN_DIR . 'assets/js',
        ONLYMATT_AI_PLUGIN_DIR . 'templates'
    );

    foreach ($dirs as $dir) {
        if (!file_exists($dir)) {
            wp_mkdir_p($dir);
        }
    }
}

// Deactivation hook
register_deactivation_hook(__FILE__, 'onlymatt_ai_deactivate');
function onlymatt_ai_deactivate() {
    // Cleanup if needed
}