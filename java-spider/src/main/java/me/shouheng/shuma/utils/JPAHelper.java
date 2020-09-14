package me.shouheng.shuma.utils;

import cn.hutool.core.util.StrUtil;
import lombok.AllArgsConstructor;
import me.shouheng.shuma.anno.ColumnDefinition;
import me.shouheng.shuma.anno.TableDefinition;

import javax.persistence.Column;
import javax.persistence.Id;
import javax.persistence.Table;
import java.lang.reflect.Field;
import java.util.Date;
import java.util.LinkedList;
import java.util.List;

/**
 * @author shouh, 2019/3/31-11:08
 */
public class JPAHelper {

    /**
     * 获取 PO 对应的表名
     *
     * @param type PO 类
     * @return     表名
     */
    public static String getTableName(Class<?> type) {
        if (!type.isAnnotationPresent(Table.class)) {
            throw new IllegalArgumentException("can't get table name.");
        }
        return type.getAnnotation(Table.class).name();
    }

    /**
     * 获取数据库表的备注信息
     *
     * @param type PO 类
     * @return     表的备注
     */
    public static String getTableComment(Class<?> type) {
        if (!type.isAnnotationPresent(TableDefinition.class)) {
            return "";
        }
        return type.getAnnotation(TableDefinition.class).comment();
    }

    /**
     * 根据 PO 类的字段，获取对应的 Mybatis 类型，
     * 参考：<a href="http://www.mybatis.org/mybatis-3/zh/configuration.html">MyBatis 官方文档-配置</a>
     *
     * @param field 字段
     * @return MyBatis 类型
     */
    public static String getMybatisType(Field field) {
        String res = "VARCHAR";
        Class type = field.getType();
        if (type == String.class) {
            res = "VARCHAR";
        } else if (type == Double.class || type == double.class) {
            res = "DOUBLE";
        } else if (type == Float.class || type == float.class) {
            res = "FLOAT";
        } else if (type == Boolean.class || type == boolean.class) {
            res = "BIT";
        } else if (type == Byte.class || type == byte.class) {
            res = "TINYINT";
        } else if (type == Short.class || type == short.class) {
            res = "SMALLINT";
        } else if (type == Integer.class || type == int.class) {
            res = "INTEGER";
        } else if (type == Date.class || type == Long.class || type == long.class) {
            res = "BIGINT";
        } else if (type.getSuperclass() == Enum.class) {
            return "SMALLINT";
        }
        return res;
    }

    /**
     * 根据 PO 类的字段，获取对应的 MySQL 列的类型
     * 参考：<a href="https://juejin.im/post/5a12d62bf265da431d3c4a01">MySQL基础知识-数据库类型</a>
     *
     * @param f 字段
     * @param type 字段类型
     * @return 对应的 MySQL 列的类型
     */
    public static String getColumnType(Field f, Class type) {
        String columnType;
        if (f.isAnnotationPresent(Column.class)
                && !StrUtil.isEmpty(f.getAnnotation(Column.class).columnDefinition())) {
            // 如果定义在Column中定义了列的数据类型，就使用指定的数据类型
            columnType = f.getAnnotation(Column.class).columnDefinition();
        } else if (f.isAnnotationPresent(Id.class)) {
            columnType = "BIGINT UNSIGNED";
        } else {
            if (Integer.class == type) {
                // 整数类型
                columnType = "INT UNSIGNED";
            } else if (Long.class == type) {
                // 长整型
                columnType = "BIGINT UNSIGNED";
            } else if (Short.class == type) {
                columnType = "SMALLINT UNSIGNED";
            } else if (Float.class == type || Double.class == type) {
                // 浮点类型
                columnType = "DOUBLE(19,4)";
            } else if (Boolean.class == type) {
                // 布尔类型
                columnType = "TINYINT(1)";
            } else if (Date.class == type) {
                // 日期类型
                columnType = "BIGINT UNSIGNED";
            } else if (Enum.class == type.getSuperclass()) {
                // 枚举类型使用 SMALLINT
                columnType = "SMALLINT";
            } else if (f.isAnnotationPresent(Column.class) && f.getAnnotation(Column.class).length() != 255) {
                columnType = "VARCHAR(" + f.getAnnotation(Column.class).length() + ")";
            } else {
                // 此外全部是字符串类型
                columnType = "VARCHAR(255)";
            }
        }
        return columnType;
    }

    /**
     * 获取整个 PO 对象对应的列的信息
     *
     * @param clazz PO 类
     * @return 列信息列表
     */
    public static List<ColumnModel> getColumnModels(Class clazz) {
        List<ColumnModel> columnModels = new LinkedList<>();
        List<Field> fields = ReflectionUtil.getAllFields(clazz, ReflectionUtil.FieldsOrder.CHILDREN_2_PARENT);
        String columnName;
        for (Field f : fields) {
            columnName = f.getName();
            if ("serialVersionUID".equalsIgnoreCase(columnName)) {
                continue;
            }
            final String finalColumnName = columnName;
            columnModels.add(
                    new ColumnModel(
                            f.getName(),
                            f.getType(),
                            f.isAnnotationPresent(Column.class) ? f.getAnnotation(Column.class).name() : finalColumnName,
                            getColumnType(f, f.getType()),
                            getMybatisType(f),
                            f.isAnnotationPresent(ColumnDefinition.class) ? f.getAnnotation(ColumnDefinition.class).comment() : "",
                            f.getAnnotation(Column.class).nullable(),
                            f.isAnnotationPresent(ColumnDefinition.class) && f.getAnnotation(ColumnDefinition.class).added()
                    )
            );
        }

        // 将 id 移动到第一个位置
        int index = 0;
        for (ColumnModel columnModel : columnModels) {
            if ("id".equalsIgnoreCase(columnModel.columnName)) {
                break;
            }
            index++;
        }
        ColumnModel idColumnModel = columnModels.remove(index);
        columnModels.add(0, idColumnModel);
        return columnModels;
    }

    /**
     * PO 对象的列信息
     */
    @AllArgsConstructor
    public static class ColumnModel {

        /**
         * 字段名称，即 {@link Field#getName()} 的值
         */
        public final String prop;

        /**
         * 字段类型，即 {@link Field#getType()} 的值
         */
        public final Class<?> propType;

        /**
         * 数据库列名，即 {@link Column#name()} 的值，或者默认使用 {@link Field#getName()} 的值
         */
        public final String columnName;

        /**
         * 数据库类型，即对应数据库列的类型，通过 {@link JPAHelper#getColumnType(Field, Class)} 得到
         */
        public final String columnType;

        /**
         * MyBatis 类型，通过 {@link JPAHelper#getMybatisType(Field)} 得到
         */
        public final String mybatisType;

        /**
         * 列的备注，通过 {@link ColumnDefinition#comment()} 得到
         */
        public final String columnComment;

        /**
         * 是否可以是空的
         */
        public final boolean nullable;

        /**
         * 是否是新增加的字段，标记了 true 的字段表示新加入，
         * 在生成 SQL 的时候会自动生成添加数据库列的 SQL 语句
         */
        public final boolean added;
    }

}
