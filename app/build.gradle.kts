plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

android {
    namespace = "com.titan.pro"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.titan.pro.v80"
        minSdk = 26
        targetSdk = 34
        versionCode = 90
        versionName = "90.0.0-embedded"

        // Native Python interpreter + wheels for real devices + emulator
        ndk {
            abiFilters += listOf("armeabi-v7a", "arm64-v8a", "x86", "x86_64")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
        debug {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

chaquopy {
    defaultConfig {
        // 3.11 supports 32-bit + 64-bit ABIs
        version = "3.11"
        pip {
            // All analysis deps live INSIDE the APK — no Termux, no external install
            install("numpy==1.26.4")
            install("pandas==2.1.4")
            install("requests==2.31.0")
            install("flask==3.0.0")
            install("waitress==3.0.0")
            install("websocket-client==1.6.4")
            install("certifi")
            install("urllib3")
            install("charset-normalizer")
            install("idna")
            install("python-dateutil")
            install("pytz")
            install("tzdata")
            install("six")
            install("werkzeug")
            install("jinja2")
            install("markupsafe")
            install("itsdangerous")
            install("click")
            install("blinker")
        }
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.webkit:webkit:1.10.0")
}
