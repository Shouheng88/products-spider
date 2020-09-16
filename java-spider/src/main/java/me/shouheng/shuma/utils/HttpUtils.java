package me.shouheng.shuma.utils;

import cn.hutool.core.util.StrUtil;
import okhttp3.*;

import java.io.IOException;

public class HttpUtils {

    private static OkHttpClient client = new OkHttpClient();

    public static void request(String pageUrl, OnGetPageContentResult result) {
        Request request = new Request.Builder().url(pageUrl).build();
        Call call = client.newCall(request);
        call.enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                if (result != null) {
                    result.onFail(ErrorCode.REQUEST_FAILED.code, "" + e);
                }
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                ResponseBody responseBody = response.body();
                String content;
                if (responseBody != null && !StrUtil.isEmpty((content = responseBody.string()))) {
                    if (result != null) {
                        result.onSuccess(content);
                    }
                } else {
                    result.onFail(ErrorCode.CONTENT_EMRTY.code, "empty");
                }
            }
        });
    }

    public enum ErrorCode {
        REQUEST_FAILED("-1"),
        CONTENT_EMRTY("-2");

        public final String code;

        ErrorCode(String code) {
            this.code = code;
        }
    }

    public interface OnGetPageContentResult {
        void onFail(String code, String message);
        void onSuccess(String content);
    }
}
