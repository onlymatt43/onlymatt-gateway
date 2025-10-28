<?php
define( 'WP_CACHE', true );

/**
 * The base configuration for WordPress
 *
 * The wp-config.php creation script uses this file during the installation.
 * You don't have to use the web site, you can copy this file to "wp-config.php"
 * and fill in the values.
 *
 * This file contains the following configurations:
 *
 * * Database settings
 * * Secret keys
 * * Database table prefix
 * * Localized language
 * * ABSPATH
 *
 * @link https://wordpress.org/support/article/editing-wp-config-php/
 *
 * @package WordPress
 */

// ** Database settings - You can get this info from your web host ** //
/** The name of the database for WordPress */
define( 'DB_NAME', 'u948138067_91N5J' );

/** Database username */
define( 'DB_USER', 'u948138067_SPTD1' );

/** Database password */
define( 'DB_PASSWORD', '4MYQLUj20B' );

/** Database hostname */
define( 'DB_HOST', '127.0.0.1' );

/** Database charset to use in creating database tables. */
define( 'DB_CHARSET', 'utf8' );

/** The database collate type. Don't change this if in doubt. */
define( 'DB_COLLATE', '' );

/**#@+
 * Authentication unique keys and salts.
 *
 * Change these to different unique phrases! You can generate these using
 * the {@link https://api.wordpress.org/secret-key/1.1/salt/ WordPress.org secret-key service}.
 *
 * You can change these at any point in time to invalidate all existing cookies.
 * This will force all users to have to log in again.
 *
 * @since 2.6.0
 */
define( 'AUTH_KEY',          'D:dNeojpgdc{KD{8&Xv]iOJ/J<UA)81F9}?Eb>b$H`%ksu:V]vE:q=`o;HrI*PHy' );
define( 'SECURE_AUTH_KEY',   'E?%&<t>)crBloJFyO=oq%rTaNB?;[@cN%XT/oD>~@lsdx-63SjuT]z.V2z,5g/dO' );
define( 'LOGGED_IN_KEY',     'f`lQ5D,zedv1W9R$v5~h7R$nM0w!|yIW$Lr^3?i;60!>;c`ntB$4;,MI2|gr*9G_' );
define( 'NONCE_KEY',         '-I<{`LHgmZf#:r,(Fv#b~ee~foKA]G!1cJJgz$<Gu(l8}%gz?W.vUBmT1>*;I58u' );
define( 'AUTH_SALT',         '>D|Bwaft$Vjxg$ftTz:w56)B7XaI;=LVnyZ<59<GdMM^{ @>/YaP?:&KwsB1prHl' );
define( 'SECURE_AUTH_SALT',  'eR5y}9ntnG{0AQE0Tpu.5Gr1}G?wV|%z*A~Pq>SILpiJ*Dz8`)nI(ya(L7D{!V45' );
define( 'LOGGED_IN_SALT',    'd;:O_8Ty-a/2gcj]E,/]we/DHSPOOC>]5j_Mry<SeaxHh${3OF`!d,K?Zw23X$#;' );
define( 'NONCE_SALT',        'y7[dI3Q9<Y;gQOROUwUqOL8I0avx>*tyt)aSDJv2@X<1lZ$f*DU1xj&xj$>A^dm`' );
define( 'WP_CACHE_KEY_SALT', 'BB*,+a(:UN:(A}q8$5/HpcNtj8;;t@.(OBh&{s>V($9.P6FRZ+pmk#xuIQ3_O>QQ' );


/**#@-*/

/**
 * WordPress database table prefix.
 *
 * You can have multiple installations in one database if you give each
 * a unique prefix. Only numbers, letters, and underscores please!
 */
$table_prefix = 'wp_';


/* Add any custom values between this line and the "stop editing" line. */



/**
 * For developers: WordPress debugging mode.
 *
 * Change this to true to enable the display of notices during development.
 * It is strongly recommended that plugin and theme developers use WP_DEBUG
 * in their development environments.
 *
 * For information on other constants that can be used for debugging,
 * visit the documentation.
 *
 * @link https://wordpress.org/support/article/debugging-in-wordpress/
 */
if ( ! defined( 'WP_DEBUG' ) ) {
	define( 'WP_DEBUG', false );
}

define( 'FS_METHOD', 'direct' );
define( 'COOKIEHASH', '600e406bad284e8e59ceec64f030ea1f' );
define( 'WP_AUTO_UPDATE_CORE', 'minor' );
define('WP_DEBUG', true);
define('WP_DEBUG_LOG', true);
define('WP_DEBUG_DISPLAY', false);
define('WP_DISABLE_FATAL_ERROR_HANDLER', true);
/* That's all, stop editing! Happy publishing. */

/** Absolute path to the WordPress directory. */
if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH', __DIR__ . '/' );
}

/** Sets up WordPress vars and included files. */
require_once ABSPATH . 'wp-settings.php';
