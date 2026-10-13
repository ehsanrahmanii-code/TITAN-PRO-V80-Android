package com.titan.pro

import android.annotation.SuppressLint
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.View
import android.webkit.WebChromeClient
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import java.util.concurrent.Executors

/**
 * Same boot pattern as working TITAN-V75-Full-Android:
 * start engine in background → wait_ready up to 180s → load WebView.
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var progress: ProgressBar
    private lateinit var status: TextView
    private val io = Executors.newSingleThreadExecutor()
    private val ui = Handler(Looper.getMainLooper())
    private var started = false

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        progress = findViewById(R.id.progress)
        status = findViewById(R.id.status)

        val s = webView.settings
        s.javaScriptEnabled = true
        s.domStorageEnabled = true
        s.databaseEnabled = true
        s.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        s.useWideViewPort = true
        s.loadWithOverviewMode = true
        s.cacheMode = WebSettings.LOAD_DEFAULT
        s.userAgentString = s.userAgentString + " TITAN-PRO-V80-Full"

        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                if (url != null && (url.contains("127.0.0.1") || url.contains("localhost"))) {
                    progress.visibility = View.GONE
                    status.visibility = View.GONE
                }
            }
        }

        bootEngine()
    }

    private fun bootEngine() {
        progress.visibility = View.VISIBLE
        status.visibility = View.VISIBLE
        status.text = "در حال راه‌اندازی موتور TITAN PRO V80…"
        io.execute {
            try {
                if (!Python.isStarted()) {
                    Python.start(AndroidPlatform(this))
                }
                val py = Python.getInstance()
                val boot = py.getModule("titan_bootstrap")
                if (!started) {
                    boot.callAttr("start_server", filesDir.absolutePath)
                    started = true
                }
                ui.post { status.text = "منتظر داشبورد Flask… (ممکن است ۱–۲ دقیقه طول بکشد)" }
                val ready = boot.callAttr("wait_ready", "http://127.0.0.1:8080/health", 180.0).toBoolean()
                ui.post {
                    progress.visibility = View.GONE
                    if (ready) {
                        status.visibility = View.GONE
                        webView.loadUrl("http://127.0.0.1:8080/")
                    } else {
                        val err = try {
                            boot.callAttr("last_error").toString()
                        } catch (_: Exception) {
                            ""
                        }
                        status.visibility = View.VISIBLE
                        status.text = "موتور بالا نیامد.\n$err"
                        Toast.makeText(this, "Engine timeout", Toast.LENGTH_LONG).show()
                        webView.loadUrl("http://127.0.0.1:8080/")
                    }
                }
            } catch (e: Exception) {
                ui.post {
                    progress.visibility = View.GONE
                    status.visibility = View.VISIBLE
                    status.text = "خطای موتور:\n${e.message}"
                    Toast.makeText(this, e.message ?: "error", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack() else super.onBackPressed()
    }
}
