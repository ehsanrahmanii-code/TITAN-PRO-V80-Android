package com.titan.pro

import android.annotation.SuppressLint
import android.os.Bundle
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

/**
 * Fully self-contained TITAN PRO app.
 * Python + numpy + pandas + flask run INSIDE the APK via Chaquopy.
 * No Termux. No external shell. No user pip install.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var progress: ProgressBar
    private lateinit var status: TextView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.webview)
        progress = findViewById(R.id.progress)
        status = findViewById(R.id.status)
        setupWebView()
        startEmbeddedEngine()
    }

    private fun setupWebView() {
        val s = webView.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.databaseEnabled = true
        s.allowFileAccess = true
        s.allowContentAccess = true
        s.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        s.cacheMode = WebSettings.LOAD_DEFAULT
        s.userAgentString = s.userAgentString + " TitanProEmbedded/90.0.0"
        webView.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(view: WebView?, newProgress: Int) {
                progress.progress = newProgress
                progress.visibility = if (newProgress in 1..99) View.VISIBLE else View.GONE
            }
        }
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                return false
            }
        }
    }

    private fun startEmbeddedEngine() {
        status.visibility = View.VISIBLE
        status.text = getString(R.string.status_preparing)
        Thread {
            try {
                if (!Python.isStarted()) {
                    Python.start(AndroidPlatform(this))
                }
                val py = Python.getInstance()
                val boot = py.getModule("titan_bootstrap")
                val filesDir = filesDir.absolutePath
                val result = boot.callAttr("start_server", filesDir).toString()

                // Wait until /health answers
                var ready = false
                repeat(40) {
                    try {
                        val url = java.net.URL("http://127.0.0.1:8080/health")
                        val conn = url.openConnection() as java.net.HttpURLConnection
                        conn.connectTimeout = 500
                        conn.readTimeout = 500
                        conn.requestMethod = "GET"
                        if (conn.responseCode == 200) {
                            ready = true
                            conn.disconnect()
                            return@repeat
                        }
                        conn.disconnect()
                    } catch (_: Exception) {
                    }
                    Thread.sleep(250)
                }

                runOnUiThread {
                    status.visibility = View.GONE
                    if (ready) {
                        webView.loadUrl("http://127.0.0.1:8080/")
                    } else {
                        status.visibility = View.VISIBLE
                        status.text = getString(R.string.status_error, "server: $result")
                        webView.loadUrl("http://127.0.0.1:8080/")
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    status.visibility = View.VISIBLE
                    status.text = getString(R.string.status_error, e.message ?: e.toString())
                }
            }
        }.start()
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
