package com.spotlight.adb;

import org.openqa.selenium.Capabilities;
import org.openqa.selenium.Platform;
import org.openqa.selenium.WebDriverException;
import org.openqa.selenium.grid.data.CreateSessionRequest;
import org.openqa.selenium.grid.node.ActiveSession;
import org.openqa.selenium.grid.node.SessionFactory;
import org.openqa.selenium.internal.Either;
import org.openqa.selenium.remote.DesiredCapabilities;
import org.openqa.selenium.remote.http.HttpClient;
import org.openqa.selenium.remote.tracing.Tracer;

import java.io.IOException;
import java.util.Map;

public class AdbSessionFactory implements SessionFactory {
    private final Tracer tracer;
    private final HttpClient.Factory clientFactory;

    public AdbSessionFactory(Tracer tracer, HttpClient.Factory clientFactory) {
        this.tracer = tracer;
        this.clientFactory = clientFactory;
    }

    @Override
    public Capabilities getStereotype() {
        System.out.println("[AdbSessionFactory] getStereotype() called, returning chrome capability");
        // 只声明 chrome 能力，不包含 adbDeviceId
        return new DesiredCapabilities("chrome", "138", Platform.valueOf("linux"));
    }

    @Override
    public boolean test(Capabilities capabilities) {
        boolean match = "chrome".equalsIgnoreCase(capabilities.getBrowserName())
            && capabilities.asMap().containsKey("se:adbDeviceId");
        System.out.println("[AdbSessionFactory] test() called, browserName=" + capabilities.getBrowserName() + ", adbDeviceId=" + capabilities.asMap().get("adbDeviceId") + ", match=" + match);
        return match;
    }

    @Override
    public Either<WebDriverException, ActiveSession> apply(CreateSessionRequest req) {
        System.out.println("[AdbSessionFactory] apply() called, processing new session request");
        Map<String, Object> caps = req.getDesiredCapabilities().asMap();
        String adbDeviceId = (String) caps.get("adbDeviceId");
        if (adbDeviceId != null && !adbDeviceId.isEmpty()) {
            System.out.println("[AdbSessionFactory] adbDeviceId found: " + adbDeviceId + ", executing adb connect...");
            try {
                Process process = Runtime.getRuntime().exec("adb connect " + adbDeviceId);
                int exitCode = process.waitFor();
                System.out.println("[AdbSessionFactory] adb connect exit code: " + exitCode);
            } catch (IOException | InterruptedException e) {
                System.out.println("[AdbSessionFactory] adb connect failed: " + e.getMessage());
                throw new WebDriverException("ADB连接失败: " + adbDeviceId, e);
            }
        } else {
            System.out.println("[AdbSessionFactory] adbDeviceId is null or empty, skipping adb connect.");
        }
        // 这里建议委托给原生SessionFactory，实际生产环境应注入原生工厂
        throw new UnsupportedOperationException("请用装饰器模式委托给原生SessionFactory");
    }
}