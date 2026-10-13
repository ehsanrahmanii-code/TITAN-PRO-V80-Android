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
        versionCode = 91
        versionName = "91.0.0-embedded"

        ndk {
            // Real phones + emulator; keeps APK large with native Python
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    buildTypes {
        release { isMinifyEnabled = false }
        debug { isMinifyEnabled = false }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions { jvmTarget = "17" }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

chaquopy {
    defaultConfig {
        version = "3.11"
        buildPython("python3.11")
        pip {
            // Libraries compiled INTO the APK
            install("numpy")
            install("pandas")
            install("requests")
            install("flask")
            install("waitress")
            install("websocket-client")
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
