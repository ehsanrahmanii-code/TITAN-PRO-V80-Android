plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.chaquo.python")
}

import java.util.Properties
import java.io.FileInputStream

android {
    namespace = "com.titan.pro"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.titan.pro.v80"
        minSdk = 26
        targetSdk = 35
        versionCode = 92
        versionName = "92.0.0-a15"

        // Xiaomi / real phones are arm64
        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }

    signingConfigs {
        create("release") {
            val ks = file("../titan-release.keystore")
            if (ks.exists()) {
                storeFile = ks
                storePassword = "titanpro80"
                keyAlias = "titan"
                keyPassword = "titanpro80"
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            isShrinkResources = false
            signingConfig = signingConfigs.getByName("release")
        }
        debug {
            isMinifyEnabled = false
            // also sign debug with release key so Xiaomi accepts install
            val rel = signingConfigs.findByName("release")
            if (rel != null && rel.storeFile != null && rel.storeFile!!.exists()) {
                signingConfig = rel
            }
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions { jvmTarget = "17" }

    packaging {
        jniLibs {
            // Required on many Xiaomi / HyperOS builds for native Python libs
            useLegacyPackaging = true
        }
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
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    implementation("androidx.webkit:webkit:1.11.0")
}
