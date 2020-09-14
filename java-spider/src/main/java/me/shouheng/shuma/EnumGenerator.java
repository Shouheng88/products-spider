package me.shouheng.shuma;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.lang.annotation.*;
import java.lang.reflect.InvocationTargetException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.stream.Stream;

/**
 * 生成 MyBatis 的枚举类型处理器
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-02  23:17
 */
@EnumGenerator.GeneratorConfiguration(
        enums = {

        },
        returnValuesWhenNull = {
                0
        },
        outputDirectory = "beauty-data/src/main/java/me/shouheng/data/dao/handler",
        author = "<a href=\"mailto:shouheng2015@gmail.com\">WngShhng</a>"
)
public final class EnumGenerator {

    private static String outputDirectory;

    private static String author;

    private static Map<Class, Integer> map = new HashMap<>();

    public static void main(String ...args) {
        // 要进行生成的枚举
        GeneratorConfiguration configuration = EnumGenerator.class.getAnnotation(GeneratorConfiguration.class);
        if (configuration == null) {
            System.err.println("错误：需要通过 @GeneratorConfiguration 注解对生成器进行配置！");
            return;
        }
        // 读取注解信息
        outputDirectory = configuration.outputDirectory();
        author = configuration.author();
        Class[] enums = configuration.enums();
        int[] values = configuration.returnValuesWhenNull();
        if (enums.length != values.length) {
            System.err.println("错误：配置注解中的枚举类型的数量应该与默认值的数量相同！");
            return;
        }
        for (int i=0, len=enums.length; i<len; i++) {
            if (values[i] != GeneratorConfiguration.NULL_CONSTANT) {
                map.put(enums[i], values[i]);
            }
        }
        Stream.of(configuration.enums()).forEach(EnumGenerator::genForEnum);
    }

    private static void genForEnum(Class enumClass) {
        String classSimpleName = enumClass.getSimpleName();
        String componentName = String.format("%sTypeHandler", classSimpleName);
        // 当读取到的值为空的时候返回的枚举类型
        String returnValueWhenNull;
        if (map.containsKey(enumClass)) {
            int defValue = map.get(enumClass);
            try {
                Enum en = (Enum) enumClass.getMethod("getTypeById", int.class).invoke(null, defValue);
                returnValueWhenNull = classSimpleName + "." + en.name();
            } catch (NoSuchMethodException e) {
                System.err.println("错误：你的枚举需要至少包含一个 getTypeById(int) 方法来根据枚举自定义 id 获取枚举实例！");
                return;
            } catch (IllegalAccessException | InvocationTargetException e) {
                e.printStackTrace();
                return;
            }
        } else {
            returnValueWhenNull = "null";
        }
        String content = header(componentName) +
                String.format("@MappedTypes(value = {%s.class})\n", classSimpleName) +
                String.format("public class %s extends BaseTypeHandler<%s> {\n\n", componentName, classSimpleName) +
                "    @Override\n" +
                String.format("    public void setNonNullParameter(PreparedStatement ps, int i, %s parameter, JdbcType jdbcType) throws SQLException {\n", classSimpleName) +
                "        ps.setInt(i, parameter.id);\n" +
                "    }" + "\n" +
                "\n" +
                "    @Override\n" +
                String.format("    public %s getNullableResult(ResultSet rs, String columnName) throws SQLException {\n", classSimpleName) +
                "        try {\n" +
                "            int id = rs.getInt(columnName);\n" +
                String.format("            return %s.getTypeById(id);\n", classSimpleName) +
                "        } catch (Exception ex) {\n" +
                String.format("            return %s;\n", returnValueWhenNull) +
                "        }\n" +
                "    }\n" +
                "\n" +
                "    @Override\n" +
                String.format("    public %s getNullableResult(ResultSet rs, int columnIndex) throws SQLException {\n", classSimpleName) +
                "        if (rs.wasNull()) {\n" +
                String.format("            return %s;\n", returnValueWhenNull) +
                "        } else {\n" +
                "            int id = rs.getInt(columnIndex);\n" +
                String.format("            return %s.getTypeById(id);\n", classSimpleName) +
                "        }\n" +
                "    }\n" +
                "\n" +
                "    @Override\n" +
                String.format("    public %s getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {\n", classSimpleName) +
                "        if (cs.wasNull()) {\n" +
                String.format("            return %s;\n", returnValueWhenNull) +
                "        } else {\n" +
                "            int id = cs.getInt(columnIndex);\n" +
                String.format("            return %s.getTypeById(id);\n", classSimpleName) +
                "        }\n" +
                "    }\n" +
                "}\n";
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
            File file = new File(dir, String.format("%sTypeHandler.java", classSimpleName));
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

    private static String header(String classComment) {
        return String.format(
                "/**\n" +
                        " * %s\n" +
                        " *\n" +
                        " * @author " + author + "\n" +
                        " * @version %s\n" +
                        " */\n", classComment, new SimpleDateFormat("yyy/MM/dd hh:mm").format(new Date()));
    }

    @Documented
    @Retention(RetentionPolicy.RUNTIME)
    @Target(value = {ElementType.TYPE})
    @interface GeneratorConfiguration {

        int NULL_CONSTANT = -3864;

        /**
         * 要来生成的枚举
         *
         * @return 枚举数组
         */
        Class[] enums();

        /**
         * 当读取到的值为 null 的时候返回的值，当前塞入的值是枚举的 id 字段，
         * 比如 {@link me.shouheng.common.model.enums.Status}
         * 默认的值是 {@link me.shouheng.common.model.enums.Status#NORMAL}，
         * 则设置值为 {@link me.shouheng.common.model.enums.Status#NORMAL#id}
         * 当设置的值为 {@link #NULL_CONSTANT} 的时候表示直接返回 null 即可。
         *
         * 该数组的长度应该与 {@link #enums()} 返回的数组的长度相同。
         *
         * @return 返回值
         */
        int[] returnValuesWhenNull();

        /**
         * 输出枚举 Handler 的文件的位置
         *
         * @return 文件的位置
         */
        String outputDirectory();

        /**
         * 创建者信息，默认为空，为空的时候创建文件时不添加创建者和版本等信息注释
         *
         * @return 创作者
         */
        String author() default "";
    }
}
