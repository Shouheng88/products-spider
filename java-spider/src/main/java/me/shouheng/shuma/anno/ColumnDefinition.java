package me.shouheng.shuma.anno;

import java.lang.annotation.*;

/**
 * 自定义注解，数据库列的备注
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019/9/22 10:43
 */
@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target(value = {ElementType.FIELD})
public @interface ColumnDefinition {

    /**
     * 备注的内容
     *
     * @return 备注的内容
     */
    String comment() default "";

    /**
     * 该字段是否属于新加的字段 对于新加的字段，可以在生成 SQL 的时候，可以自动生成添加列的 SQL 语句
     *
     * @return true 表示新添加的字段
     */
    boolean added() default false;

    /**
     * 是否生成该类的 schema 类，schema 类是一个枚举类，其中的枚举值是 po 对象的各个字段的枚举值
     *
     * @return true 表示生成 schema 枚举值
     */
    boolean genSchema() default false;
}
