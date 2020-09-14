package me.shouheng.shuma.utils;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 抽象的生成器
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2020/1/29 12:57
 */
public abstract class BaseGenerator {

    protected static String convertFirstLetterToLower(String className) {
        String lowerString;
        String firstLetter = className.substring(0, 1);
        String leftLetters = className.substring(1);

        lowerString = firstLetter.toLowerCase() + leftLetters;
        return lowerString;
    }

    protected static String header(String author, String classComment) {
        return String.format(
                "/**\n" +
                        " * %s\n" +
                        " *\n" +
                        " * @author " + author + "\n" +
                        " * @version %s\n" +
                        " */\n", classComment, new SimpleDateFormat("yyy/MM/dd hh:mm").format(new Date()));
    }

    protected static String header(String pkg, String author, String classComment) {
        return String.format(pkg +
                "\n\n" +
                "/**\n" +
                " * %s\n" +
                " *\n" +
                " * @author " + author + "\n" +
                " * @version %s\n" +
                " */\n", classComment, new SimpleDateFormat("yyy/MM/dd hh:mm").format(new Date()));
    }

    protected static void printFile(String fileName, String content, String  outputDirectory, boolean coverExistFiles) {
        System.out.println(content);
        File dir = new File(outputDirectory);
        if (!dir.exists()) {
            boolean succeed = dir.mkdir();
            if (!succeed) {
                System.out.println("创建目录失败");
                return;
            }
        }

        FileWriter fw = null;
        BufferedWriter bw = null;
        try {
            File file = new File(dir, fileName);
            if (file.exists() && !coverExistFiles) {
                System.err.println("重要：要写入的文件已经存在，谨慎覆盖导致内容丢失！");
                return;
            }
            fw = new FileWriter(file);
            bw = new BufferedWriter(fw);
            bw.write(content);
        } catch (IOException ex) {
            ex.printStackTrace();
        } finally {
            try {
                if (bw != null) {
                    bw.close();
                }
                if (fw != null) {
                    fw.close();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    protected static void printFile(String fileName, String content, String  outputDirectory) {
        printFile(fileName, content, outputDirectory, true);
    }
}
